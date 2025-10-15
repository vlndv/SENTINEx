// =================================================================================================
// OnePoundCloserPro — XAUUSD-only | OnTick | Fee Floor | Hard Cash Stop-Loss
// Closes when NetProfit >= max(TargetProfitMoney, FeeFloorMoney)  [TP path]
// OR when NetProfit <= -MaxLossMoney                              [SL path, bypasses spread/min-hold]
// Scope: MANAGES ONLY XAUUSD positions.
// Built for [Valentino – V1N]
// =================================================================================================

using cAlgo.API;
using cAlgo.API.Internals;
using System;
using System.Collections.Generic;

namespace cAlgo
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class OnePoundCloserPro : Robot
    {
        // ============================
        // PARAMETERS
        // ============================

        [Parameter("Target Profit (Acct Currency)", Group = "Logic", DefaultValue = 1.20)]
        public double TargetProfitMoney { get; set; }   // Desired TP per position (net)

        [Parameter("Fee Floor (Min Net to Close)", Group = "Risk Controls", DefaultValue = 1.00)]
        public double FeeFloorMoney { get; set; }       // Never close winners below this net

        [Parameter("Max Loss (Acct Currency)", Group = "Risk Controls", DefaultValue = 3.00)]
        public double MaxLossMoney { get; set; }        // Hard cash stop per position (net loss)

        [Parameter("Only Manual Positions", Group = "Filters", DefaultValue = true)]
        public bool OnlyManualPositions { get; set; }   // Empty/whitespace label (or whitelist) = manual

        [Parameter("Manual Label Must Contain", Group = "Filters", DefaultValue = "")]
        public string ManualLabelWhitelist { get; set; }

        [Parameter("Use Spread Guard (for TP only)", Group = "Risk Controls", DefaultValue = false)]
        public bool UseSpreadGuard { get; set; }

        [Parameter("Max Spread (points)", Group = "Risk Controls", DefaultValue = 80)]
        public int MaxSpreadPoints { get; set; }

        [Parameter("Use Min Hold Time (for TP only)", Group = "Risk Controls", DefaultValue = false)]
        public bool UseMinHoldMs { get; set; }

        [Parameter("Min Hold Time (ms)", Group = "Risk Controls", DefaultValue = 1200)]
        public int MinHoldMs { get; set; }

        [Parameter("Check Interval (ms)", Group = "Engine", DefaultValue = 200)]
        public int CheckIntervalMs { get; set; }

        [Parameter("Retries On Close Fail", Group = "Engine", DefaultValue = 1, MinValue = 0, MaxValue = 5)]
        public int RetryCount { get; set; }

        [Parameter("Retry Delay (ms)", Group = "Engine", DefaultValue = 150, MinValue = 50, MaxValue = 1000)]
        public int RetryDelayMs { get; set; }

        [Parameter("Dry Run (No Actual Close)", Group = "Diagnostics", DefaultValue = false)]
        public bool DryRun { get; set; }

        [Parameter("Verbose Logs (Diagnostics)", Group = "Diagnostics", DefaultValue = true)]
        public bool Verbose { get; set; }

        // ============================
        // STATE
        // ============================

        private readonly HashSet<long> _closing = new HashSet<long>();
        private readonly Dictionary<long, DateTime> _openedAt = new Dictionary<long, DateTime>();

        // ============================
        // LIFECYCLE
        // ============================

        protected override void OnStart()
        {
            if (TargetProfitMoney <= 0) { Print("[OPC] TargetProfitMoney must be > 0. Stopping."); Stop(); return; }
            if (FeeFloorMoney < 0) { Print("[OPC] FeeFloorMoney must be >= 0. Stopping."); Stop(); return; }
            if (MaxLossMoney <= 0) { Print("[OPC] MaxLossMoney must be > 0. Stopping."); Stop(); return; }
            if (UseMinHoldMs && MinHoldMs < 0) { Print("[OPC] MinHoldMs must be >= 0. Stopping."); Stop(); return; }
            if (UseSpreadGuard && MaxSpreadPoints <= 0) { Print("[OPC] MaxSpreadPoints must be > 0. Stopping."); Stop(); return; }

            // Seed open times for existing positions
            foreach (var p in Positions)
                _openedAt[p.Id] = p.EntryTime.ToUniversalTime();

            // Events + timer
            Positions.Opened += Positions_Opened;
            Positions.Closed += Positions_Closed;
            Timer.Start(CheckIntervalMs);

            var asset = Account.Asset.Name;
            Print($"[OPC] Started | SYMBOL SCOPE = XAUUSD ONLY | TP={TargetProfitMoney} {asset} | Floor={FeeFloorMoney} {asset} | SL={MaxLossMoney} {asset} | " +
                  $"SpreadGuard={(UseSpreadGuard ? MaxSpreadPoints + "pts" : "off")} | MinHold={(UseMinHoldMs ? MinHoldMs + "ms" : "off")} | " +
                  $"Retries={RetryCount}x{RetryDelayMs}ms | DryRun={DryRun} | Verbose={Verbose}");

            TryManagePositions();
        }

        protected override void OnStop()
        {
            Positions.Opened -= Positions_Opened;
            Positions.Closed -= Positions_Closed;
            _closing.Clear();
            _openedAt.Clear();
            Print("[OPC] Stopped.");
        }

        // Low-latency scan
        protected override void OnTick() => TryManagePositions();
        protected override void OnTimer() => TryManagePositions();

        // ============================
        // EVENTS
        // ============================

        private void Positions_Opened(PositionOpenedEventArgs args)
        {
            _openedAt[args.Position.Id] = args.Position.EntryTime.ToUniversalTime();
            if (Verbose) Print($"[OPC] Opened #{args.Position.Id} {args.Position.SymbolName} label='{args.Position.Label ?? "<empty>"}'");
            TryManagePositions();
        }

        private void Positions_Closed(PositionClosedEventArgs args)
        {
            bool botDidIt = _closing.Contains(args.Position.Id);
            _closing.Remove(args.Position.Id);
            _openedAt.Remove(args.Position.Id);

            var asset = Account.Asset.Name;
            if (botDidIt)
                Print($"[OPC] Closed by bot #{args.Position.Id} Realized={args.Position.NetProfit:F2} {asset}");
            else if (Verbose)
                Print($"[OPC] External close detected #{args.Position.Id} Realized={args.Position.NetProfit:F2} {asset}");
        }

        // ============================
        // CORE
        // ============================

        private void TryManagePositions()
        {
            try
            {
                double effTP = Math.Max(TargetProfitMoney, FeeFloorMoney);

                foreach (var pos in Positions)
                {
                    // Manage ONLY XAUUSD
                    if (!string.Equals(pos.SymbolName, "XAUUSD", StringComparison.OrdinalIgnoreCase))
                    {
                        if (Verbose) Print($"[Skip] #{pos.Id} {pos.SymbolName} — not XAUUSD.");
                        continue;
                    }

                    // Manual-only filter
                    if (OnlyManualPositions && !IsManualLabel(pos.Label))
                    {
                        if (Verbose) Print($"[Skip] #{pos.Id} label='{(pos.Label ?? "<null>")}' not manual; set OnlyManual=false or whitelist.");
                        continue;
                    }

                    // ======================
                    // 1) HARD STOP-LOSS PATH
                    // ======================
                    if (pos.NetProfit <= -MaxLossMoney)
                    {
                        if (_closing.Contains(pos.Id)) continue; // already handling
                        _closing.Add(pos.Id);
                        // SL bypasses spread/min-hold: get out
                        bool closedSL = CloseWithRetry(pos, effTP, reason: "SL");
                        if (!closedSL) _closing.Remove(pos.Id);
                        continue; // next position
                    }

                    // ======================
                    // 2) TAKE-PROFIT PATH
                    // ======================
                    // Optional min-hold for TP
                    if (UseMinHoldMs && !HasHeldLongEnough(pos))
                    {
                        if (Verbose) Print($"[Skip] #{pos.Id} age<{MinHoldMs}ms");
                        continue;
                    }

                    // Optional spread guard for TP
                    if (UseSpreadGuard && !SpreadOk(pos.SymbolName))
                    {
                        if (Verbose) Print($"[Skip] #{pos.Id} spread>limit {MaxSpreadPoints}pts");
                        continue;
                    }

                    // TP trigger
                    if (pos.NetProfit >= effTP)
                    {
                        if (_closing.Contains(pos.Id))
                        {
                            if (Verbose) Print($"[Hold] #{pos.Id} already closing");
                            continue;
                        }

                        _closing.Add(pos.Id);
                        bool closedTP = CloseWithRetry(pos, effTP, reason: "TP");
                        if (!closedTP) _closing.Remove(pos.Id);
                    }
                    else if (Verbose)
                    {
                        Print($"[Trace] #{pos.Id} XAUUSD Net={pos.NetProfit:F2} / TP={effTP:F2} / SL={-MaxLossMoney:F2} {Account.Asset.Name} " +
                              $"(target={TargetProfitMoney:F2}, floor={FeeFloorMoney:F2})");
                    }
                }
            }
            catch (Exception ex)
            {
                Print($"[OPC] Exception in TryManagePositions: {ex.Message}");
            }
        }

        // ============================
        // HELPERS
        // ============================

        private bool IsManualLabel(string label)
        {
            bool emptyOrWs = string.IsNullOrWhiteSpace(label);
            if (!string.IsNullOrWhiteSpace(ManualLabelWhitelist))
            {
                string safe = label ?? string.Empty;
                return emptyOrWs || safe.IndexOf(ManualLabelWhitelist, StringComparison.OrdinalIgnoreCase) >= 0;
            }
            return emptyOrWs;
        }

        private bool HasHeldLongEnough(Position pos)
        {
            if (!UseMinHoldMs) return true;
            if (!_openedAt.TryGetValue(pos.Id, out var openedUtc))
                openedUtc = pos.EntryTime.ToUniversalTime();
            return (DateTime.UtcNow - openedUtc).TotalMilliseconds >= MinHoldMs;
        }

        private bool SpreadOk(string symbolName)
        {
            var s = Symbols.GetSymbol(symbolName);
            double spreadPoints = Math.Abs((s.Ask - s.Bid) / s.TickSize);
            if (Verbose) Print($"[Spread] {symbolName} = {spreadPoints:F0} pts (max {MaxSpreadPoints})");
            return spreadPoints <= MaxSpreadPoints;
        }

        private bool CloseWithRetry(Position pos, double effTargetForLog, string reason)
        {
            if (DryRun)
            {
                Print($"[DRY-RUN][{reason}] Would close {pos.SymbolName} {pos.TradeType} #{pos.Id} at Net={pos.NetProfit:F2} {Account.Asset.Name} " +
                      $"(effTP={effTargetForLog:F2}, floor={FeeFloorMoney:F2}, target={TargetProfitMoney:F2}, SL={MaxLossMoney:F2})");
                return true;
            }

            int attempts = 0;
            while (true)
            {
                attempts++;
                var res = ClosePosition(pos);

                if (res.IsSuccessful)
                {
                    Print($"[OPC][{reason}] Closed {pos.SymbolName} {pos.TradeType} #{pos.Id} Net={pos.NetProfit:F2} {Account.Asset.Name} " +
                          $"(attempt {attempts}, effTP={effTargetForLog:F2}, floor={FeeFloorMoney:F2}, target={TargetProfitMoney:F2}, SL={MaxLossMoney:F2})");
                    return true;
                }

                if (attempts <= RetryCount)
                {
                    if (Verbose) Print($"[Retry][{reason}] Close failed #{pos.Id}: {res.Error}. Retry in {RetryDelayMs}ms");
                    Sleep(RetryDelayMs);
                    continue;
                }

                Print($"[OPC][{reason}] Close FAILED #{pos.Id} after {attempts} attempts. Error: {res.Error}");
                return false;
            }
        }
    }
}
