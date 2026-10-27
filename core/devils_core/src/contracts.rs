//! Contratos Vivos: modificadores declarativos con duracion. Se ofrecen 3; cada uno altera UNA sola cosa y
//! muestra duracion, beneficio, riesgo y restricciones antes de aceptar. Nunca alteran las cartas repartidas.
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ContractKind { BrokenHeart, Mirror, Chains, BlazingBet, HouseListens, SealedTable, HonorDebt, DoubleOrNothing }

impl ContractKind {
    pub const ALL: [ContractKind; 8] = [ContractKind::BrokenHeart, ContractKind::Mirror, ContractKind::Chains, ContractKind::BlazingBet,
        ContractKind::HouseListens, ContractKind::SealedTable, ContractKind::HonorDebt, ContractKind::DoubleOrNothing];
    /// Contratos de alto riesgo: perder uno cuesta Pulso en el sistema de campana.
    pub fn high_risk(self) -> bool { matches!(self, ContractKind::DoubleOrNothing | ContractKind::BrokenHeart) }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Contract {
    pub kind: ContractKind,
    pub duration: u8,
    pub remaining: u8,
    /// Bonificacion en % sobre la ganancia neta (Apuesta Ardiente). 0 si no aplica.
    pub bonus_pct: i64,
    /// Exposicion adicional permitida en % sobre la apuesta maxima (contrapartida de Apuesta Ardiente).
    pub exposure_pct: i64,
    pub negotiated: bool,
    /// Clausula original guardada por La Contadora si Vespera la altero: (bonus_pct, exposure_pct).
    #[serde(default)]
    pub original: Option<(i64, i64)>,
}

impl Contract {
    pub fn new(kind: ContractKind, duration: u8) -> Contract {
        let (bonus_pct, exposure_pct) = if kind == ContractKind::BlazingBet { (50, 50) } else { (0, 0) };
        Contract { kind, duration, remaining: duration, bonus_pct, exposure_pct, negotiated: false, original: None }
    }
}

/// Resultado de una mano visto por los contratos.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct HandResult { pub won: bool, pub net: i64, pub bet: i64 }

/// Efectos producidos tras una mano.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Effects {
    pub bonus_chips: i64,
    pub fund_bonus: i64,
    pub seal_memory: bool,
    pub narrative_question: bool,
    pub personal_answer_due: bool,
    pub extra_inspection: bool,
    pub requirement_to_collect: bool,
    pub expired: Vec<ContractKind>,
    pub high_risk_lost: bool,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ContractBook {
    pub active: Vec<Contract>,
    chain_wins: u8,
    mirror_ready: bool,
    pub memory_cards_disabled: bool,
    pub offers_made: u32,
}

pub const REJECT_COST: i64 = 5;

impl ContractBook {
    /// Genera 3 ofertas distintas. Los pesos dependen del estado (fichas bajas, racha, acto).
    pub fn offer(&mut self, seed: u64, act: u8, chips: i64, loss_streak: u32) -> [Contract; 3] {
        self.offers_made += 1;
        let mut rng = ChaCha8Rng::seed_from_u64(seed ^ (self.offers_made as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15));
        let mut pool: Vec<ContractKind> = ContractKind::ALL.to_vec();
        pool.retain(|k| *k != ContractKind::DoubleOrNothing || act >= 2);
        pool.shuffle(&mut rng);
        // Con pocas fichas o racha perdedora se favorece un contrato de bajo riesgo (Casa Escucha / Cadenas).
        if (chips < 50 || loss_streak >= 3) && !pool[..3].iter().any(|k| !k.high_risk()) {
            let i = pool.iter().position(|k| !k.high_risk()).unwrap();
            pool.swap(2, i);
        }
        let dur = |k: ContractKind, rng: &mut ChaCha8Rng| -> u8 {
            use rand::Rng;
            match k { ContractKind::Mirror | ContractKind::SealedTable => 1, _ => if rng.gen_range(0..10) == 0 { 3 } else { rng.gen_range(1..=2) } }
        };
        let mut v = vec![];
        for k in &pool[..3] { let d = dur(*k, &mut rng); v.push(Contract::new(*k, d)); }
        [v[0].clone(), v[1].clone(), v[2].clone()]
    }

    pub fn accept(&mut self, c: Contract) -> Result<(), String> {
        if !self.active.is_empty() { return Err("ya hay un contrato activo".into()); }
        if c.kind == ContractKind::SealedTable { self.memory_cards_disabled = true; }
        if c.kind == ContractKind::Mirror { self.mirror_ready = true; }
        self.active.push(c);
        Ok(())
    }

    /// Rechazar las tres ofertas cuesta una cantidad pequena y conocida.
    pub fn reject_all(&self, chips: i64) -> Result<i64, String> {
        if chips < REJECT_COST { Ok(0) } else { Ok(REJECT_COST) }
    }

    /// Negociar: cambia UNA condicion (menos recompensa a cambio de menor riesgo). Consume un Favor (lo gestiona la economia).
    pub fn negotiate(c: &mut Contract) {
        if c.negotiated { return; }
        c.negotiated = true;
        c.bonus_pct /= 2;
        c.exposure_pct /= 2;
        if c.duration > 1 { c.duration -= 1; c.remaining = c.duration; }
    }

    /// Trampa contractual: Vespera altera la clausula del contrato activo (reduce la ganancia, sube la exposicion).
    pub fn alter_active(&mut self) -> bool {
        match self.active.first_mut() {
            Some(c) if c.original.is_none() => { c.original = Some((c.bonus_pct, c.exposure_pct)); c.bonus_pct /= 2; c.exposure_pct += 25; true }
            _ => false,
        }
    }
    /// Si se detecta, se restaura la clausula original.
    pub fn restore_active(&mut self) -> bool {
        match self.active.first_mut() {
            Some(c) => match c.original.take() { Some((b, e)) => { c.bonus_pct = b; c.exposure_pct = e; true } None => false },
            None => false,
        }
    }

    pub fn mirror_peek_available(&self) -> bool { self.mirror_ready }
    pub fn use_mirror_peek(&mut self) -> bool { std::mem::replace(&mut self.mirror_ready, false) }

    /// Maxima apuesta efectiva con contratos activos.
    pub fn effective_max_bet(&self, base_max: i64) -> i64 {
        let extra: i64 = self.active.iter().map(|c| c.exposure_pct).sum();
        base_max + base_max * extra / 100
    }

    pub fn after_hand(&mut self, r: HandResult) -> Effects {
        let mut fx = Effects::default();
        for c in &mut self.active {
            match c.kind {
                ContractKind::BlazingBet => if r.won { fx.bonus_chips += r.net.max(0) * c.bonus_pct / 100 },
                ContractKind::BrokenHeart => {
                    if r.won { fx.bonus_chips += r.net.max(0); c.remaining = 0; } // recompensa doble en la proxima victoria
                    else { fx.seal_memory = true; fx.high_risk_lost = true; }
                }
                ContractKind::Chains => {
                    if r.won { self.chain_wins += 1; if self.chain_wins >= 2 { fx.fund_bonus += r.bet; self.chain_wins = 0; c.remaining = 0; } }
                    else { self.chain_wins = 0; }
                }
                ContractKind::HouseListens => if r.won { fx.narrative_question = true } else { fx.personal_answer_due = true },
                ContractKind::HonorDebt => if r.won { fx.extra_inspection = true } else { fx.requirement_to_collect = true },
                ContractKind::DoubleOrNothing => {
                    if r.won { fx.bonus_chips += r.net.max(0); c.remaining = 0; } else { fx.high_risk_lost = true; c.remaining = 0; }
                }
                ContractKind::Mirror | ContractKind::SealedTable => {}
            }
            c.remaining = c.remaining.saturating_sub(1).min(c.remaining);
        }
        let mut expired = vec![];
        self.active.retain(|c| { if c.remaining == 0 { expired.push(c.kind); false } else { true } });
        for k in &expired { if *k == ContractKind::SealedTable { self.memory_cards_disabled = false; } if *k == ContractKind::Mirror { self.mirror_ready = false; } }
        fx.expired = expired;
        fx
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn win(net: i64) -> HandResult { HandResult { won: true, net, bet: net } }
    fn loss(bet: i64) -> HandResult { HandResult { won: false, net: -bet, bet } }

    #[test]
    fn three_distinct_offers_and_deterministic() {
        let mut a = ContractBook::default();
        let mut b = ContractBook::default();
        let oa = a.offer(5, 1, 1000, 0);
        assert_eq!(oa, b.offer(5, 1, 1000, 0));
        assert!(oa[0].kind != oa[1].kind && oa[1].kind != oa[2].kind && oa[0].kind != oa[2].kind);
        assert!(oa.iter().all(|c| (1..=3).contains(&c.duration)));
    }

    #[test]
    fn double_or_nothing_not_in_act_one() {
        for s in 0..300 {
            let mut b = ContractBook::default();
            assert!(b.offer(s, 1, 1000, 0).iter().all(|c| c.kind != ContractKind::DoubleOrNothing));
        }
    }

    #[test]
    fn low_chips_always_get_a_low_risk_offer() {
        for s in 0..300 {
            let mut b = ContractBook::default();
            assert!(b.offer(s, 3, 20, 4).iter().any(|c| !c.kind.high_risk()));
        }
    }

    #[test]
    fn one_active_contract_only() {
        let mut b = ContractBook::default();
        b.accept(Contract::new(ContractKind::Chains, 2)).unwrap();
        assert!(b.accept(Contract::new(ContractKind::Chains, 2)).is_err());
    }

    #[test]
    fn blazing_bet_bonus_and_exposure() {
        let mut b = ContractBook::default();
        b.accept(Contract::new(ContractKind::BlazingBet, 2)).unwrap();
        assert_eq!(b.effective_max_bet(500), 750);
        let fx = b.after_hand(win(100));
        assert_eq!(fx.bonus_chips, 50);
        assert_eq!(b.active.len(), 1);
        let fx = b.after_hand(loss(100));
        assert_eq!(fx.bonus_chips, 0);
        assert_eq!(fx.expired, vec![ContractKind::BlazingBet]);
        assert_eq!(b.effective_max_bet(500), 500);
    }

    #[test]
    fn broken_heart_doubles_next_win_or_seals_memory() {
        let mut b = ContractBook::default();
        b.accept(Contract::new(ContractKind::BrokenHeart, 2)).unwrap();
        let fx = b.after_hand(win(80));
        assert_eq!(fx.bonus_chips, 80);
        assert!(b.active.is_empty());
        let mut c = ContractBook::default();
        c.accept(Contract::new(ContractKind::BrokenHeart, 2)).unwrap();
        let fx = c.after_hand(loss(50));
        assert!(fx.seal_memory && fx.high_risk_lost);
    }

    #[test]
    fn chains_pays_fund_after_two_straight_wins() {
        let mut b = ContractBook::default();
        b.accept(Contract::new(ContractKind::Chains, 3)).unwrap();
        assert_eq!(b.after_hand(win(10)).fund_bonus, 0);
        assert_eq!(b.after_hand(win(10)).fund_bonus, 10);
        let mut c = ContractBook::default();
        c.accept(Contract::new(ContractKind::Chains, 3)).unwrap();
        c.after_hand(win(10));
        c.after_hand(loss(10));
        assert_eq!(c.after_hand(win(10)).fund_bonus, 0);
    }

    #[test]
    fn sealed_table_disables_memory_cards_until_expiry() {
        let mut b = ContractBook::default();
        b.accept(Contract::new(ContractKind::SealedTable, 1)).unwrap();
        assert!(b.memory_cards_disabled);
        b.after_hand(win(10));
        assert!(!b.memory_cards_disabled);
    }

    #[test]
    fn mirror_gives_one_peek_only() {
        let mut b = ContractBook::default();
        b.accept(Contract::new(ContractKind::Mirror, 1)).unwrap();
        assert!(b.use_mirror_peek());
        assert!(!b.use_mirror_peek());
    }

    #[test]
    fn house_listens_and_honor_debt_flags() {
        let mut b = ContractBook::default();
        b.accept(Contract::new(ContractKind::HouseListens, 2)).unwrap();
        assert!(b.after_hand(win(10)).narrative_question);
        assert!(b.after_hand(loss(10)).personal_answer_due);
        let mut c = ContractBook::default();
        c.accept(Contract::new(ContractKind::HonorDebt, 1)).unwrap();
        assert!(c.after_hand(win(10)).extra_inspection);
    }

    #[test]
    fn negotiation_trades_reward_for_less_risk_once() {
        let mut c = Contract::new(ContractKind::BlazingBet, 2);
        ContractBook::negotiate(&mut c);
        assert_eq!((c.bonus_pct, c.exposure_pct, c.duration), (25, 25, 1));
        ContractBook::negotiate(&mut c);
        assert_eq!((c.bonus_pct, c.exposure_pct, c.duration), (25, 25, 1));
    }

    #[test]
    fn reject_cost_is_small_and_known() {
        let b = ContractBook::default();
        assert_eq!(b.reject_all(100).unwrap(), REJECT_COST);
        assert_eq!(b.reject_all(0).unwrap(), 0);
    }
}
