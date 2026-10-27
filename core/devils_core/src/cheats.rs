//! Trampas verificables: el estado se COMPROMETE (hash) antes de resolver; toda trampa es un evento explicito
//! con su pista; `Inspeccionar la Mesa` compara estado comprometido contra el mostrado. Nada cambia el resultado sin rastro.
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CheatKind { SwappedCard, CursedDeck, ForbiddenGaze, AlteredContract, GhostCard, AlteredBet }

impl CheatKind {
    pub const ALL: [CheatKind; 6] = [CheatKind::SwappedCard, CheatKind::CursedDeck, CheatKind::ForbiddenGaze,
        CheatKind::AlteredContract, CheatKind::GhostCard, CheatKind::AlteredBet];
    /// Acto minimo (1..=5) en el que puede aparecer.
    pub fn min_act(self) -> u8 {
        match self {
            CheatKind::AlteredBet | CheatKind::SwappedCard => 1,
            CheatKind::GhostCard | CheatKind::AlteredContract => 2,
            CheatKind::CursedDeck => 3,
            CheatKind::ForbiddenGaze => 4,
        }
    }
}

/// Hash FNV-1a 64 estable (no depende de la version de Rust).
pub fn fnv1a(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in bytes { h ^= *b as u64; h = h.wrapping_mul(0x100000001b3); }
    h
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CheatRecord {
    pub round: u64,
    pub kind: CheatKind,
    pub committed: u64,
    pub shown: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Inspection {
    /// Acusacion correcta: se anula/corrige, compensacion y 1 Prueba.
    Correct(CheatKind),
    /// Habia trampa pero se acuso otra cosa o ninguna en ese tipo.
    Wrong,
    /// No hubo trampa en esa ronda.
    Clean,
    /// Sin cargas.
    NoCharges,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CheatLedger {
    pub records: Vec<CheatRecord>,
    pub charges: u8,
    pub proofs: u32,
    pending_commit: Option<(u64, u64)>, // (round, hash)
    last_cheat_round: Option<u64>,
}

pub const CHARGES_PER_ACT: u8 = 2;

impl Default for CheatLedger {
    fn default() -> Self { CheatLedger { records: vec![], charges: CHARGES_PER_ACT, proofs: 0, pending_commit: None, last_cheat_round: None } }
}

impl CheatLedger {
    pub fn new_act(&mut self) { self.charges = CHARGES_PER_ACT; }

    /// Compromete el estado ANTES de resolver la ronda.
    pub fn commit(&mut self, round: u64, state_hash: u64) { self.pending_commit = Some((round, state_hash)); }

    /// Decide (sin tocar las cartas) si en esta ronda habria trampa y de que tipo. Reglas:
    /// frecuencia sube con el acto y las emociones; nunca dos rondas seguidas; nunca en la primera ronda.
    pub fn roll(&self, seed: u64, round: u64, act: u8, frequency_pct: i32) -> Option<CheatKind> {
        if round == 0 || self.last_cheat_round == Some(round.wrapping_sub(1)) { return None; }
        let mut rng = ChaCha8Rng::seed_from_u64(seed ^ round.wrapping_mul(0xA24B_AED4_963E_E407));
        let base = [0, 4, 8, 12, 18, 25][act.clamp(1, 5) as usize]; // % por ronda
        let p = (base * frequency_pct.max(0) / 100).min(40);
        if rng.gen_range(0..100) >= p { return None; }
        let allowed: Vec<CheatKind> = CheatKind::ALL.into_iter().filter(|k| k.min_act() <= act).collect();
        if allowed.is_empty() { return None; }
        Some(allowed[rng.gen_range(0..allowed.len())])
    }

    /// Registra una trampa ejecutada: el hash mostrado difiere del comprometido (o no, si es de contrato/apuesta).
    pub fn record(&mut self, round: u64, kind: CheatKind, shown_hash: u64) -> Result<(), String> {
        let committed = match self.pending_commit { Some((r, h)) if r == round => h, _ => return Err("sin compromiso previo".into()) };
        self.records.push(CheatRecord { round, kind, committed, shown: shown_hash });
        self.last_cheat_round = Some(round);
        Ok(())
    }

    /// Inspeccionar la Mesa: el jugador acusa un tipo en una ronda. Consume una carga.
    pub fn inspect(&mut self, round: u64, accused: CheatKind) -> Inspection {
        if self.charges == 0 { return Inspection::NoCharges; }
        self.charges -= 1;
        match self.records.iter().position(|r| r.round == round) {
            None => Inspection::Clean,
            Some(i) if self.records[i].kind == accused => {
                self.proofs += 1;
                let k = self.records[i].kind;
                self.records[i].shown = self.records[i].committed; // se restaura el estado original
                Inspection::Correct(k)
            }
            Some(_) => Inspection::Wrong,
        }
    }

    /// Con suficientes pruebas se puede exigir una mano supervisada por La Contadora.
    pub fn can_demand_supervision(&self) -> bool { self.proofs >= 3 }

    pub fn cheat_in_round(&self, round: u64) -> Option<&CheatRecord> { self.records.iter().find(|r| r.round == round) }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fnv_is_stable() {
        assert_eq!(fnv1a(b""), 0xcbf29ce484222325);
        assert_eq!(fnv1a(b"a"), 0xaf63dc4c8601ec8c);
    }

    #[test]
    fn requires_prior_commit() {
        let mut l = CheatLedger::default();
        assert!(l.record(1, CheatKind::SwappedCard, 5).is_err());
        l.commit(1, 99);
        assert!(l.record(2, CheatKind::SwappedCard, 5).is_err());
        assert!(l.record(1, CheatKind::SwappedCard, 5).is_ok());
        assert_eq!(l.records[0].committed, 99);
    }

    #[test]
    fn inspection_outcomes() {
        let mut l = CheatLedger::default();
        l.commit(3, 1);
        l.record(3, CheatKind::GhostCard, 2).unwrap();
        assert_eq!(l.inspect(4, CheatKind::GhostCard), Inspection::Clean);
        assert_eq!(l.inspect(3, CheatKind::AlteredBet), Inspection::Wrong);
        assert_eq!(l.inspect(3, CheatKind::GhostCard), Inspection::NoCharges);
        l.new_act();
        assert_eq!(l.inspect(3, CheatKind::GhostCard), Inspection::Correct(CheatKind::GhostCard));
        assert_eq!(l.proofs, 1);
        assert_eq!(l.records[0].shown, l.records[0].committed);
    }

    #[test]
    fn failed_inspection_costs_only_a_charge() {
        let mut l = CheatLedger::default();
        l.inspect(1, CheatKind::SwappedCard);
        assert_eq!(l.charges, CHARGES_PER_ACT - 1);
        assert_eq!(l.proofs, 0);
    }

    #[test]
    fn roll_is_deterministic_and_respects_act() {
        let l = CheatLedger::default();
        for r in 1..2000 {
            assert_eq!(l.roll(7, r, 3, 100), l.roll(7, r, 3, 100));
            if let Some(k) = l.roll(7, r, 1, 100) { assert!(k.min_act() <= 1); }
        }
        assert_eq!(l.roll(7, 0, 5, 100), None);
    }

    #[test]
    fn frequency_rises_with_act_and_never_exceeds_cap() {
        let l = CheatLedger::default();
        let n = |act| (1..20000u64).filter(|&r| l.roll(11, r, act, 100).is_some()).count();
        assert!(n(1) < n(3) && n(3) < n(5));
        assert!(n(5) < 20000 * 41 / 100);
    }

    #[test]
    fn never_two_consecutive_cheats() {
        let mut l = CheatLedger::default();
        let mut last = false;
        for r in 1..5000u64 {
            let cheat = l.roll(3, r, 5, 150);
            if cheat.is_some() {
                assert!(!last, "trampas seguidas en ronda {r}");
                l.commit(r, 0);
                l.record(r, cheat.unwrap(), 1).unwrap();
            }
            last = cheat.is_some();
        }
    }

    #[test]
    fn supervision_needs_three_proofs() {
        let mut l = CheatLedger::default();
        l.proofs = 2;
        assert!(!l.can_demand_supervision());
        l.proofs = 3;
        assert!(l.can_demand_supervision());
    }
}
