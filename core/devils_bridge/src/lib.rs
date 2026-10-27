//! Puente gdext: expone `devils_core::Table` a Godot. Todo cruza como JSON (comandos simples, eventos y estado en String).
use devils_core::side_bets::SideBetKind;
use devils_core::contracts::Contract;
use devils_core::cheats::CheatKind;
use devils_core::game::{Game, InspectReport, MemoryReveal};
use devils_core::memory_cards::MemoryCard;
use devils_core::{Action, Card, Phase, TableRules};
use godot::prelude::*;
use serde_json::{json, Value};

struct DevilsExtension;

#[gdextension]
unsafe impl ExtensionLibrary for DevilsExtension {}

#[derive(GodotClass)]
#[class(base = RefCounted)]
pub struct DevilsTable {
    table: Option<Game>,
    offers: Vec<Contract>,
    base: Base<RefCounted>,
}

#[godot_api]
impl IRefCounted for DevilsTable {
    fn init(base: Base<RefCounted>) -> Self { DevilsTable { table: None, offers: vec![], base } }
}

fn codes(cs: &[Card]) -> Vec<String> { cs.iter().map(|c| c.code()).collect() }

fn ok(v: Value) -> GString { GString::from(&v.to_string()) }
fn err(e: impl std::fmt::Display) -> GString { ok(json!({ "error": e.to_string() })) }

impl DevilsTable {
    fn t(&mut self) -> Result<&mut Game, String> { self.table.as_mut().ok_or_else(|| "mesa no creada".to_string()) }
    fn events(&mut self, ev: &[devils_core::Event]) -> GString {
        let ce = self.table.as_mut().map(|g| std::mem::take(&mut g.campaign_events)).unwrap_or_default();
        ok(json!({ "events": ev, "campaign_events": ce }))
    }
    fn card_id(id: &GString) -> Result<MemoryCard, String> { serde_json::from_value(json!(id.to_string())).map_err(|_| "carta desconocida".to_string()) }
}

#[godot_api]
impl DevilsTable {
    /// `rules_json` puede ser "{}" (reglas por defecto) o parcial. Devuelve "{}" o {"error":...}.
    #[func]
    fn new_game(&mut self, rules_json: GString, chips: i64, seed: i64) -> GString {
        let rules: TableRules = match serde_json::from_str(&rules_json.to_string()) { Ok(r) => r, Err(e) => return err(e) };
        let _ = chips; // las fichas iniciales las fija la economia (100)
        match Game::new(rules, seed as u64) {
            Ok(t) => { self.table = Some(t); ok(json!({})) }
            Err(e) => err(e),
        }
    }

    /// `side_json`: {"triblack":25,"blackseven":0}
    #[func]
    fn start_round(&mut self, bet: i64, side_json: GString) -> GString {
        let side: Value = serde_json::from_str(&side_json.to_string()).unwrap_or(json!({}));
        let mut sides = vec![];
        if let Some(a) = side["triblack"].as_i64() { sides.push((SideBetKind::TriBlack, a)); }
        if let Some(a) = side["blackseven"].as_i64() { sides.push((SideBetKind::BlackSeven, a)); }
        match self.t().and_then(|t| t.start_round(bet, &sides)) { Ok(ev) => self.events(&ev), Err(e) => err(e) }
    }

    #[func]
    fn insurance(&mut self, stake: i64) -> GString {
        match self.t().and_then(|t| t.insurance(stake)) { Ok(ev) => self.events(&ev), Err(e) => err(e) }
    }

    /// action: "hit" | "stand" | "double" | "split" | "surrender"
    #[func]
    fn act(&mut self, action: GString) -> GString {
        let a = match action.to_string().as_str() {
            "hit" => Action::Hit, "stand" => Action::Stand, "double" => Action::Double,
            "split" => Action::Split, "surrender" => Action::Surrender,
            other => return err(format!("accion desconocida: {other}")),
        };
        match self.t().and_then(|t| t.act(a)) { Ok(ev) => self.events(&ev), Err(e) => err(e) }
    }

    /// Estado visible para el jugador (la carta oculta del crupier no se incluye).
    #[func]
    fn state(&mut self) -> GString {
        let g = match self.t() { Ok(g) => g, Err(e) => return err(e) };
        let t = &g.table;
        let hands: Vec<Value> = t.hands().iter().map(|h| json!({
            "cards": codes(&h.cards), "value": h.value(), "soft": h.is_soft(), "bet": h.bet,
            "status": h.status, "outcome": h.outcome, "payout": h.payout, "doubled": h.doubled })).collect();
        let phase = match t.phase() { Phase::Idle => "idle", Phase::Insurance => "insurance", Phase::PlayerTurn => "player", Phase::Finished => "finished" };
        let legal: Vec<String> = t.legal_actions().iter().map(|a| format!("{:?}", a).to_lowercase()).collect();
        let active: Vec<Value> = g.contracts.active.iter().map(|c| json!(c)).collect();
        ok(json!({ "phase": phase, "chips": t.chips, "hands": hands, "active": t.active_hand(),
            "dealer": codes(t.dealer_visible()), "dealer_hidden": t.dealer_cards_all().len() > t.dealer_visible().len(),
            "legal": legal, "shoe_remaining": t.shoe().remaining(), "rounds": t.rounds_played,
            "act": g.act, "max_bet": g.max_bet(), "min_bet": t.rules.min_bet,
            "fascination": g.emotion.fascination, "despair": g.emotion.despair, "style": g.emotion.style(),
            "streak_wins": g.emotion.streak_wins, "streak_losses": g.emotion.streak_losses,
            "honor_hand_pending": g.emotion.honor_hand_pending,
            "fund": g.economy.return_fund, "seals": g.economy.seals, "pulse": g.economy.pulse, "favors": g.economy.favors,
            "contract_due": g.contract_due(), "contracts": active,
            "inspect_charges": g.cheats.charges, "proofs": g.cheats.proofs, "supervision": g.cheats.can_demand_supervision(),
            "campaign": { "act": g.campaign.act, "phase": g.campaign.phase, "normal_hands": g.campaign.normal_hands,
                "hands_per_act": devils_core::campaign::NORMAL_HANDS_PER_ACT, "duel_player": g.campaign.duel.player, "duel_dealer": g.campaign.duel.dealer,
                "ending": g.campaign.ending, "duels_lost": g.campaign.duels_lost },
            "memory": { "slots": devils_core::memory_cards::SLOTS, "sealed": g.sealed_table,
                "equipped": g.memory.equipped.iter().map(|c| json!({ "id": c, "left": g.memory.uses_left(*c), "before_deal": c.before_deal_only() })).collect::<Vec<_>>(),
                "unlocked": g.memory.unlocked } }))
    }

    #[func]
    fn unlock_memory(&mut self, id: GString) -> GString {
        let c = match Self::card_id(&id) { Ok(c) => c, Err(e) => return err(e) };
        match self.t() { Ok(g) => { g.memory.unlock(c); ok(json!({})) } Err(e) => err(e) }
    }

    #[func]
    fn equip_memory(&mut self, id: GString) -> GString {
        let c = match Self::card_id(&id) { Ok(c) => c, Err(e) => return err(e) };
        match self.t().and_then(|g| g.memory.equip(c)) { Ok(()) => ok(json!({})), Err(e) => err(e) }
    }

    #[func]
    fn unequip_memory(&mut self, id: GString) -> GString {
        let c = match Self::card_id(&id) { Ok(c) => c, Err(e) => return err(e) };
        match self.t() { Ok(g) => { g.memory.unequip(c); ok(json!({})) } Err(e) => err(e) }
    }

    /// Devuelve {"reveal": {"kind": "none|next_card|cheating|replaced", ...}} o {"error"}.
    #[func]
    fn use_memory(&mut self, id: GString) -> GString {
        let c = match Self::card_id(&id) { Ok(c) => c, Err(e) => return err(e) };
        match self.t().and_then(|g| g.use_memory(c)) {
            Ok(MemoryReveal::None) => ok(json!({ "reveal": { "kind": "none" } })),
            Ok(MemoryReveal::NextCard(k)) => ok(json!({ "reveal": { "kind": "next_card", "card": k.code() } })),
            Ok(MemoryReveal::Cheating(b)) => ok(json!({ "reveal": { "kind": "cheating", "value": b } })),
            Ok(MemoryReveal::Replaced(k)) => ok(json!({ "reveal": { "kind": "replaced", "card": k.code() } })),
            Err(e) => err(e),
        }
    }

    #[func]
    fn set_cheats(&mut self, on: bool) { if let Some(g) = self.table.as_mut() { g.cheats_enabled = on; } }

    #[func]
    fn advance_act(&mut self) { if let Some(g) = self.table.as_mut() { g.advance_act(); } }

    /// kind: swapped | cursed | gaze | contract | ghost | bet
    #[func]
    fn inspect(&mut self, kind: GString) -> GString {
        let k = match kind.to_string().as_str() {
            "swapped" => CheatKind::SwappedCard, "cursed" => CheatKind::CursedDeck, "gaze" => CheatKind::ForbiddenGaze,
            "contract" => CheatKind::AlteredContract, "ghost" => CheatKind::GhostCard, "bet" => CheatKind::AlteredBet,
            other => return err(format!("tipo desconocido: {other}")),
        };
        match self.t().and_then(|g| g.inspect(k)) {
            Ok(InspectReport::Correct { compensation, .. }) => ok(json!({ "result": "correct", "compensation": compensation })),
            Ok(InspectReport::Wrong) => ok(json!({ "result": "wrong" })),
            Ok(InspectReport::Clean) => ok(json!({ "result": "clean" })),
            Ok(InspectReport::NoCharges) => ok(json!({ "result": "no_charges" })),
            Err(e) => err(e),
        }
    }

    /// Devuelve 3 ofertas (se guardan para `accept_contract`).
    #[func]
    fn offer_contracts(&mut self) -> GString {
        let g = match self.t() { Ok(g) => g, Err(e) => return err(e) };
        let o = g.offer_contracts();
        self.offers = o.to_vec();
        ok(json!({ "offers": self.offers }))
    }

    #[func]
    fn accept_contract(&mut self, index: i64) -> GString {
        let Some(c) = self.offers.get(index as usize).cloned() else { return err("oferta inexistente") };
        match self.t().and_then(|g| g.accept_contract(c)) { Ok(_) => { self.offers.clear(); ok(json!({})) } Err(e) => err(e) }
    }

    #[func]
    fn reject_contracts(&mut self) -> GString {
        match self.t().and_then(|g| g.reject_contracts()) { Ok(_) => { self.offers.clear(); ok(json!({})) } Err(e) => err(e) }
    }

    /// Serializa la partida completa (semilla y orden del zapato incluidos).
    #[func]
    fn save_json(&mut self) -> GString {
        match self.t().and_then(|t| t.to_json()) { Ok(s) => GString::from(&s), Err(e) => err(e) }
    }

    #[func]
    fn load_json(&mut self, json: GString) -> GString {
        match Game::from_json(&json.to_string()) { Ok(t) => { self.table = Some(t); ok(json!({})) } Err(e) => err(e) }
    }
}
