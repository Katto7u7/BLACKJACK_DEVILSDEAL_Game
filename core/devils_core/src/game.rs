//! Sesion de juego: une mesa, economia, emociones, contratos y registro de trampas.
//! Las trampas aun NO alteran cartas (flag `cheats_enabled` apagado): solo se compromete el estado antes de cada ronda.
use crate::campaign::{Campaign, CampaignEvent, DuelHand, EndingInputs, Phase as CampPhase};
use crate::cards::Card;
use crate::memory_cards::{MemoryCard, MemoryDeck};
use crate::cheats::{CheatKind, CheatLedger, Inspection};
use crate::contracts::{Contract, ContractBook, Effects, HandResult};
use crate::economy::Economy;
use crate::emotion::{Emotion, EmotionEvent, HandRecord};
use crate::hand::Outcome;
use crate::rules::TableRules;
use crate::side_bets::SideBetKind;
use crate::table::{Action, Event, Hint, Phase, Table};
use serde::{Deserialize, Serialize};

pub const SAVE_VERSION: u32 = 1;
/// Manos normales por acto antes de ofrecer contrato (minimo del diseno: 3-4).
pub const HANDS_BETWEEN_CONTRACTS: u32 = 3;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Game {
    pub save_version: u32,
    pub seed: u64,
    pub act: u8,
    pub table: Table,
    pub economy: Economy,
    pub emotion: Emotion,
    pub contracts: ContractBook,
    pub cheats: CheatLedger,
    pub cheats_enabled: bool,
    pub hands_since_contract: u32,
    pub last_effects: Effects,
    #[serde(default)]
    pub campaign: Campaign,
    #[serde(default)]
    pub memory: MemoryDeck,
    /// Eventos de campana de la ultima accion (el puente los vacia).
    #[serde(default)]
    pub campaign_events: Vec<CampaignEvent>,
    /// El jugador esta en la Mesa Sellada (memorias desactivadas). Lo activa un evento/duelo.
    #[serde(default)]
    pub sealed_table: bool,
    #[serde(default)]
    silence: bool,
    #[serde(default)]
    heartbeat_shield: bool,
    #[serde(default)]
    twin_armed: bool,
    round_bet: i64,
    sabotage_hit20: bool,
    started_with_bet: bool,
    tamper: Option<Tamper>,
    gaze_armed: bool,
}

/// Registro para deshacer una trampa detectada.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Tamper {
    pub kind: CheatKind,
    pub original: Option<Card>,
    pub replaced: Option<Card>,
    /// Posicion del zapato (relativa al momento del cambio) donde quedo la carta original.
    pub shoe_slot: Option<usize>,
    pub remaining_at: usize,
    pub extra_bet: i64,
    pub dealer: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MemoryReveal { None, NextCard(Card), Cheating(bool), Replaced(Card) }

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum InspectReport { Correct { kind: CheatKind, compensation: i64 }, Wrong, Clean, NoCharges }

impl Game {
    pub fn new(rules: TableRules, seed: u64) -> Result<Game, String> {
        let economy = Economy::default();
        let table = Table::new(rules, economy.chips, seed)?;
        Ok(Game { save_version: SAVE_VERSION, seed, act: 1, table, economy, emotion: Emotion::default(), contracts: ContractBook::default(),
            cheats: CheatLedger::default(), cheats_enabled: false, hands_since_contract: 0, last_effects: Effects::default(), campaign: Campaign::default(), memory: MemoryDeck::default(),
            campaign_events: vec![], sealed_table: false, silence: false, heartbeat_shield: false, twin_armed: false,
            round_bet: 0, sabotage_hit20: false, started_with_bet: false, tamper: None, gaze_armed: false })
    }

    pub fn max_bet(&self) -> i64 { self.contracts.effective_max_bet(self.table.rules.max_bet) }

    pub fn contract_due(&self) -> bool { self.contracts.active.is_empty() && self.hands_since_contract >= HANDS_BETWEEN_CONTRACTS }

    pub fn offer_contracts(&mut self) -> [Contract; 3] {
        self.contracts.offer(self.seed, self.act, self.table.chips, self.emotion.streak_losses)
    }

    pub fn start_round(&mut self, bet: i64, side: &[(SideBetKind, i64)]) -> Result<Vec<Event>, String> {
        if self.emotion.honor_hand_pending && !self.contracts.active.is_empty() {
            return Err("Mano de Honor: sin contratos".into());
        }
        if bet > self.max_bet() { return Err("apuesta sobre el limite".into()); }
        if self.campaign.ending.is_some() { return Err("la campana termino".into()); }
        if self.campaign.phase == CampPhase::DuelDue {
            let ev = self.campaign.start_duel()?;
            self.campaign_events.extend(ev);
        }
        self.twin_armed = false;
        // La mesa valida contra su propio maximo: se amplia temporalmente si un contrato lo permite.
        let base = self.table.rules.max_bet;
        self.table.rules.max_bet = self.max_bet();
        let r = self.table.start_round(bet, side);
        self.table.rules.max_bet = base;
        let ev = r?;
        self.round_bet = bet;
        self.sabotage_hit20 = false;
        self.started_with_bet = true;
        self.cheats.commit(self.table.rounds_played, self.table.digest());
        let mut ev = ev;
        self.tamper = None;
        self.gaze_armed = false;
        if self.cheats_enabled && !self.silence && matches!(self.table.phase(), Phase::PlayerTurn | Phase::Insurance) {
            self.maybe_cheat(&mut ev);
        }
        self.silence = false;
        self.settle_if_finished(&mut ev);
        Ok(ev)
    }

    fn maybe_cheat(&mut self, ev: &mut Vec<Event>) {
        let round = self.table.rounds_played;
        let Some(kind) = self.cheats.roll(self.seed, round, self.act, self.emotion.cheat_frequency_pct()) else { return };
        if kind == CheatKind::ForbiddenGaze { self.gaze_armed = true; return; }
        self.cheats.commit(round, self.table.digest());
        let none = |kind| Tamper { kind, original: None, replaced: None, shoe_slot: None, remaining_at: 0, extra_bet: 0, dealer: false };
        let applied = match kind {
            CheatKind::SwappedCard => self.tamper_player_card(),
            CheatKind::AlteredBet => self.tamper_bet(),
            CheatKind::CursedDeck | CheatKind::GhostCard => self.tamper_dealer_hole(kind),
            CheatKind::AlteredContract => self.contracts.alter_active().then(|| none(kind)),
            CheatKind::ForbiddenGaze => None,
        };
        if let Some(t) = applied {
            let hint = match kind {
                CheatKind::SwappedCard => Hint::IrregularFingers, CheatKind::CursedDeck => Hint::ShoeGlow, CheatKind::AlteredBet => Hint::ExtraSmoke,
                CheatKind::GhostCard => Hint::MarkedBack, CheatKind::AlteredContract => Hint::InkFlicker, CheatKind::ForbiddenGaze => Hint::EyesGlow,
            };
            let shown = self.table.digest();
            let _ = self.cheats.record(round, kind, shown);
            self.tamper = Some(t);
            ev.push(Event::CheatHint { hint });
        }
    }

    fn find_upcoming(&self, pred: impl Fn(Card) -> bool) -> Option<usize> {
        (0..10).find(|&j| self.table.shoe().upcoming(j).map_or(false, &pred))
    }

    fn tamper_player_card(&mut self) -> Option<Tamper> {
        let cur = *self.table.hands()[0].cards.get(1)?;
        if self.table.hands()[0].is_blackjack() { return None; }
        let j = self.find_upcoming(|c| c.rank.value() < cur.rank.value() && c.rank.value() >= 2)?;
        let remaining_at = self.table.shoe().remaining();
        let new = self.table.shoe().upcoming(j)?;
        self.table.shoe_mut().swap_upcoming(j, cur);
        self.table.hand0_mut().cards[1] = new;
        self.table.hand0_mut().refresh_status();
        Some(Tamper { kind: CheatKind::SwappedCard, original: Some(cur), replaced: Some(new), shoe_slot: Some(j), remaining_at, extra_bet: 0, dealer: false })
    }

    fn tamper_bet(&mut self) -> Option<Tamper> {
        let extra = (self.table.hands()[0].bet / 5).max(1);
        if self.table.chips < extra { return None; }
        self.table.chips -= extra;
        self.table.hand0_mut().bet += extra;
        Some(Tamper { kind: CheatKind::AlteredBet, original: None, replaced: None, shoe_slot: None, remaining_at: 0, extra_bet: extra, dealer: false })
    }

    fn tamper_dealer_hole(&mut self, kind: CheatKind) -> Option<Tamper> {
        let hole = *self.table.dealer_cards_all().get(1)?;
        let want = if kind == CheatKind::CursedDeck { 10 } else { 8 };
        if hole.rank.value() >= want { return None; }
        let j = self.find_upcoming(|c| c.rank.value() == want || (want == 8 && c.rank.value() == 9))?;
        let remaining_at = self.table.shoe().remaining();
        let new = self.table.shoe().upcoming(j)?;
        self.table.shoe_mut().swap_upcoming(j, hole);
        self.table.dealer_mut()[1] = new;
        Some(Tamper { kind, original: Some(hole), replaced: Some(new), shoe_slot: Some(j), remaining_at, extra_bet: 0, dealer: true })
    }

    /// Inspeccionar la Mesa: solo durante la ronda en curso. Acierto: restaura, compensa 25% de la apuesta y da 1 Prueba.
    pub fn inspect(&mut self, accused: CheatKind) -> Result<InspectReport, String> {
        if !matches!(self.table.phase(), Phase::PlayerTurn | Phase::Insurance) { return Err("no hay ronda en curso".into()); }
        let round = self.table.rounds_played;
        Ok(match self.cheats.inspect(round, accused) {
            Inspection::Correct(kind) => {
                self.undo_tamper();
                let compensation = self.round_bet / 4;
                self.table.chips += compensation;
                self.economy.chips = self.table.chips;
                self.economy.fraud_proofs = self.cheats.proofs;
                InspectReport::Correct { kind, compensation }
            }
            Inspection::Wrong => InspectReport::Wrong,
            Inspection::Clean => InspectReport::Clean,
            Inspection::NoCharges => InspectReport::NoCharges,
        })
    }

    fn undo_tamper(&mut self) {
        let Some(t) = self.tamper.take() else { return };
        match t.kind {
            CheatKind::AlteredContract => { self.contracts.restore_active(); }
            CheatKind::AlteredBet => { self.table.hand0_mut().bet -= t.extra_bet; self.table.chips += t.extra_bet; }
            CheatKind::ForbiddenGaze => {
                // intercambia de nuevo la carta superior con el 10 que se coloco
                let (Some(top), Some(ten)) = (t.original, t.replaced) else { return };
                let dealt = t.remaining_at.saturating_sub(self.table.shoe().remaining());
                if dealt == 0 {
                    if let Some(j) = (1..10).find(|&j| self.table.shoe().upcoming(j) == Some(top)) {
                        self.table.shoe_mut().swap_upcoming(0, top);
                        self.table.shoe_mut().swap_upcoming(j, ten);
                    }
                }
            }
            _ => {
                let (Some(orig), Some(new), Some(j)) = (t.original, t.replaced, t.shoe_slot) else { return };
                let dealt = t.remaining_at.saturating_sub(self.table.shoe().remaining());
                if j < dealt { return; }
                self.table.shoe_mut().swap_upcoming(j - dealt, new);
                if t.dealer { self.table.dealer_mut()[1] = orig; } else { self.table.hand0_mut().cards[1] = orig; self.table.hand0_mut().refresh_status(); }
            }
        }
    }

    pub fn insurance(&mut self, stake: i64) -> Result<Vec<Event>, String> {
        let mut ev = self.table.insurance(stake)?;
        self.settle_if_finished(&mut ev);
        Ok(ev)
    }

    pub fn act(&mut self, a: Action) -> Result<Vec<Event>, String> {
        let mut pre = vec![];
        if a == Action::Hit {
            if let Some(i) = self.table.active_hand() {
                let v = self.table.hands()[i].value();
                if v >= 20 { self.sabotage_hit20 = true; }
                if self.gaze_armed && (12..=16).contains(&v) { self.apply_gaze(&mut pre); }
            }
        }
        let mut ev = self.table.act(a)?;
        pre.append(&mut ev);
        let mut ev = pre;
        self.settle_if_finished(&mut ev);
        Ok(ev)
    }

    fn apply_gaze(&mut self, ev: &mut Vec<Event>) {
        self.gaze_armed = false;
        let Some(j) = self.find_upcoming(|c| c.rank.value() == 10) else { return };
        if j == 0 { return; }
        let round = self.table.rounds_played;
        self.cheats.commit(round, self.table.digest());
        let remaining_at = self.table.shoe().remaining();
        let top = self.table.shoe().upcoming(0).unwrap();
        let ten = self.table.shoe().upcoming(j).unwrap();
        self.table.shoe_mut().swap_upcoming(0, ten);
        self.table.shoe_mut().swap_upcoming(j, top);
        let _ = self.cheats.record(round, CheatKind::ForbiddenGaze, self.table.digest());
        self.tamper = Some(Tamper { kind: CheatKind::ForbiddenGaze, original: Some(top), replaced: Some(ten), shoe_slot: Some(0), remaining_at, extra_bet: 0, dealer: false });
        ev.push(Event::CheatHint { hint: Hint::EyesGlow });
    }

    fn settle_if_finished(&mut self, _ev: &mut Vec<Event>) {
        if self.table.phase() != Phase::Finished || !self.started_with_bet { return; }
        self.started_with_bet = false;
        let hands = self.table.hands();
        let bet_total: i64 = hands.iter().map(|h| h.bet).sum();
        let payout: i64 = hands.iter().map(|h| h.payout).sum();
        let net = payout - bet_total;
        let won = net > 0;
        let surrendered = hands.iter().any(|h| h.outcome == Outcome::Surrender);
        let abandon = surrendered && self.round_bet * 2 >= self.max_bet();
        let prev_losses = self.emotion.streak_losses;
        self.emotion.record_hand(HandRecord { bet: self.round_bet, max_bet: self.table.rules.max_bet, hit_on_20_plus: self.sabotage_hit20,
            max_bet_then_abandon: abandon && self.round_bet >= self.table.rules.max_bet, won, surrendered });
        if won && prev_losses >= 3 { self.emotion.apply(EmotionEvent::Comeback); }
        else if won && hands.iter().any(|h| h.value() == 21 || h.doubled) { self.emotion.apply(EmotionEvent::TenseHandWin); }
        let fx = self.contracts.after_hand(HandResult { won, net, bet: self.round_bet });
        self.table.chips += fx.bonus_chips;
        self.economy.chips = self.table.chips;
        if fx.fund_bonus > 0 { self.economy.return_fund += fx.fund_bonus; }
        if fx.extra_inspection { self.cheats.charges = self.cheats.charges.saturating_add(1); }
        if fx.high_risk_lost { self.economy.lose_pulse(); }
        self.last_effects = fx;
        if self.twin_armed && net < 0 {
            let back = self.round_bet / 2;
            self.table.chips += back;
        }
        self.twin_armed = false;
        self.hands_since_contract += 1;
        self.economy.chips = self.table.chips;
        let first = &self.table.hands()[0];
        let result = if net > 0 { DuelHand::Win } else if net < 0 || first.outcome == Outcome::Surrender { DuelHand::Loss } else { DuelHand::Push };
        self.campaign_step(result);
        self.memory.new_hand();
        if self.emotion.honor_hand_pending { self.hands_since_contract = 0; }
    }

    fn pulse_loss(&mut self) -> bool {
        if self.heartbeat_shield && self.economy.pulse == 1 { self.heartbeat_shield = false; return false; }
        self.economy.lose_pulse()
    }

    fn campaign_step(&mut self, result: DuelHand) {
        let inputs = EndingInputs { pulse: self.economy.pulse, seals: self.economy.seals + 1, fascination: self.emotion.fascination, despair: self.emotion.despair,
            fraud_proofs: self.cheats.proofs, return_fund: self.economy.return_fund, signed_clause: false, chose_to_stay: false };
        if self.campaign.phase == CampPhase::Duel {
            let (ev, sealed, critical) = self.campaign.on_duel_hand(result, inputs);
            self.campaign_events.extend(ev);
            if sealed { self.economy.win_seal(); self.act = self.campaign.act; self.cheats.new_act(); self.memory.new_act(); self.hands_since_contract = 0; }
            if critical && self.pulse_loss() { let e = self.campaign.on_pulse_zero(); self.campaign_events.extend(e); }
        } else {
            let ev = self.campaign.on_normal_hand();
            self.campaign_events.extend(ev);
        }
        if self.economy.pulse == 0 && self.campaign.ending.is_none() { let e = self.campaign.on_pulse_zero(); self.campaign_events.extend(e); }
    }

    /// Usa una Carta de Memoria equipada. Devuelve datos de la revelacion (si la hay).
    pub fn use_memory(&mut self, c: MemoryCard) -> Result<MemoryReveal, String> {
        let dealt = !matches!(self.table.phase(), Phase::Idle | Phase::Finished);
        let in_round = matches!(self.table.phase(), Phase::PlayerTurn | Phase::Insurance);
        if !c.before_deal_only() && !in_round { return Err("solo con la ronda en curso".into()); }
        // Comprobaciones previas que no consumen la carta.
        let mut redraw: Option<(Card, Card)> = None;
        match c {
            MemoryCard::SecondChance => {
                if self.table.phase() != Phase::PlayerTurn || self.table.hands().len() != 1 { return Err("ahora no".into()); }
                let h = &self.table.hands()[0];
                if h.cards.len() < 3 { return Err("pide una carta primero".into()); }
                let old = *h.cards.last().unwrap();
                let new = self.table.shoe().upcoming(1).ok_or("zapato vacio")?;
                let mut test = h.clone();
                test.cards.pop();
                test.cards.push(new);
                if test.is_bust() { return Err("el destino no ofrece nada mejor".into()); }
                redraw = Some((old, new));
            }
            MemoryCard::ContractBreaker if self.contracts.active.is_empty() => return Err("no hay contrato activo".into()),
            _ => {}
        }
        self.memory.activate(c, self.sealed_table, dealt)?;
        let mut reveal = MemoryReveal::None;
        match c {
            MemoryCard::SecondChance => {
                let (old, new) = redraw.unwrap();
                self.table.shoe_mut().swap_upcoming(1, old);
                let h = self.table.hand0_mut();
                h.cards.pop();
                h.cards.push(new);
                h.refresh_status();
                reveal = MemoryReveal::Replaced(new);
            }
            MemoryCard::EyeOfDestiny => { if let Some(n) = self.table.shoe().upcoming(0) { reveal = MemoryReveal::NextCard(n); } }
            MemoryCard::TruthHurts => { reveal = MemoryReveal::Cheating(self.cheats.cheat_in_round(self.table.rounds_played).is_some() || self.gaze_armed); }
            MemoryCard::ContractBreaker => { self.contracts.active.clear(); }
            MemoryCard::LastHeartbeat => { self.heartbeat_shield = true; }
            MemoryCard::InfernalSilence => { self.silence = true; }
            MemoryCard::TwinChips => { self.twin_armed = true; }
        }
        Ok(reveal)
    }

    /// Acepta una oferta (el indice 0..3 lo elige el jugador). Reinicia el contador de manos.
    pub fn accept_contract(&mut self, offer: Contract) -> Result<(), String> {
        if self.emotion.honor_hand_pending { return Err("Mano de Honor pendiente: no hay contratos".into()); }
        self.contracts.accept(offer)?;
        self.hands_since_contract = 0;
        Ok(())
    }

    pub fn reject_contracts(&mut self) -> Result<(), String> {
        let cost = self.contracts.reject_all(self.table.chips)?;
        self.table.chips -= cost;
        self.economy.chips = self.table.chips;
        self.hands_since_contract = 0;
        Ok(())
    }

    /// Termina la Mano de Honor tras jugarla.
    pub fn finish_honor_hand(&mut self) { self.emotion.finish_honor_hand(); }

    pub fn advance_act(&mut self) {
        if self.act < 5 { self.act += 1; }
        self.cheats.new_act();
    }

    pub fn to_json(&self) -> Result<String, String> { serde_json::to_string(self).map_err(|e| e.to_string()) }
    pub fn from_json(s: &str) -> Result<Game, String> {
        let g: Game = serde_json::from_str(s).map_err(|e| e.to_string())?;
        if g.save_version > SAVE_VERSION { return Err("guardado de version futura".into()); }
        Ok(g)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::contracts::ContractKind;
    use crate::strategy::basic_strategy;

    fn play_out(g: &mut Game) {
        loop {
            match g.table.phase() {
                Phase::Insurance => { g.insurance(0).unwrap(); }
                Phase::PlayerTurn => {
                    let up = g.table.dealer_visible()[0];
                    let a = basic_strategy(&g.table.hands()[g.table.active_hand().unwrap()], up, &g.table.legal_actions());
                    g.act(a).unwrap();
                }
                _ => break,
            }
        }
    }

    #[test]
    fn plays_rounds_and_syncs_economy() {
        let mut g = Game::new(TableRules::default(), 11).unwrap();
        for _ in 0..30 {
            if g.table.chips < 10 || g.campaign.ending.is_some() { break; }
            g.start_round(10, &[]).unwrap();
            play_out(&mut g);
            assert_eq!(g.economy.chips, g.table.chips);
        }
        assert!(g.hands_since_contract > 0);
    }

    #[test]
    fn contract_due_after_three_hands_and_blazing_bet_raises_limit() {
        let mut g = Game::new(TableRules::default(), 3).unwrap();
        g.table.chips = 100_000;
        for _ in 0..HANDS_BETWEEN_CONTRACTS { g.start_round(10, &[]).unwrap(); play_out(&mut g); }
        assert!(g.contract_due());
        assert!(g.start_round(600, &[]).is_err());
        g.accept_contract(Contract::new(ContractKind::BlazingBet, 2)).unwrap();
        assert!(!g.contract_due());
        assert_eq!(g.max_bet(), 750);
        g.start_round(600, &[]).unwrap();
        assert_eq!(g.table.rules.max_bet, 500, "el limite base se restaura");
    }

    #[test]
    fn hitting_on_20_repeatedly_triggers_honor_hand_and_blocks_contracts() {
        let mut g = Game::new(TableRules::default(), 1).unwrap();
        g.emotion.record_hand(HandRecord { bet: 500, max_bet: 500, hit_on_20_plus: true, ..Default::default() });
        g.emotion.record_hand(HandRecord { bet: 500, max_bet: 500, hit_on_20_plus: true, ..Default::default() });
        g.emotion.record_hand(HandRecord { bet: 500, max_bet: 500, hit_on_20_plus: true, ..Default::default() });
        g.emotion.record_hand(HandRecord { bet: 500, max_bet: 500, hit_on_20_plus: true, ..Default::default() });
        assert!(g.emotion.honor_hand_pending);
        assert!(g.accept_contract(Contract::new(ContractKind::Chains, 2)).is_err());
        g.finish_honor_hand();
        assert!(g.accept_contract(Contract::new(ContractKind::Chains, 2)).is_ok());
    }

    #[test]
    fn reject_costs_five() {
        let mut g = Game::new(TableRules::default(), 2).unwrap();
        let before = g.table.chips;
        g.reject_contracts().unwrap();
        assert_eq!(g.table.chips, before - 5);
    }

    #[test]
    fn save_roundtrip_keeps_everything() {
        let mut g = Game::new(TableRules::default(), 4).unwrap();
        g.start_round(10, &[]).unwrap();
        play_out(&mut g);
        let j = g.to_json().unwrap();
        let mut h = Game::from_json(&j).unwrap();
        assert_eq!(h.table.chips, g.table.chips);
        assert_eq!(h.emotion, g.emotion);
        g.start_round(10, &[]).unwrap();
        h.start_round(10, &[]).unwrap();
        assert_eq!(g.table.hands()[0].cards, h.table.hands()[0].cards, "recargar no permite re-tirar cartas");
    }

    #[test]
    fn rejects_future_save() {
        let g = Game::new(TableRules::default(), 4).unwrap();
        let j = g.to_json().unwrap().replace("\"save_version\":1", "\"save_version\":99");
        assert!(Game::from_json(&j).is_err());
    }

    #[test]
    fn act_advance_resets_inspection_charges() {
        let mut g = Game::new(TableRules::default(), 4).unwrap();
        g.cheats.charges = 0;
        g.advance_act();
        assert_eq!((g.act, g.cheats.charges), (2, 2));
    }

    #[test]
    fn chains_contract_pays_fund_through_game() {
        let mut g = Game::new(TableRules::default(), 9).unwrap();
        g.table.chips = 100_000;
        g.accept_contract(Contract::new(ContractKind::Chains, 100)).unwrap();
        for _ in 0..200 { if g.campaign.ending.is_some() { break; } g.start_round(10, &[]).unwrap(); play_out(&mut g); }
        assert!(g.economy.return_fund > 0);
    }
}
