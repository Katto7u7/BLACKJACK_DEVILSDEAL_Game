//! Estado emocional de Vespera: Fascinacion, Desesperacion, Desden (oculto) y memoria de decisiones.
//! Afecta dialogo, contratos y frecuencia de trampas; NUNCA las cartas repartidas sin trampa explicita.
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum EmotionEvent {
    Comeback,          // remontada tras racha perdedora
    TenseHandWin,      // victoria en mano tensa
    UnexpectedWin,
    SmartNegotiation,
    MeaninglessDuel,   // baja fascinacion
    Contempt,
    SealWon,           // sube desesperacion
    FundDeposit,
    TruthFound,
    IntentToLeave,
}

/// Resumen de una mano para detectar autoboicot.
#[derive(Clone, Copy, Debug, Default)]
pub struct HandRecord {
    pub bet: i64,
    pub max_bet: i64,
    /// Pidio carta con 20 o mas (apuesta contra si mismo).
    pub hit_on_20_plus: bool,
    /// Apostó el maximo y abandono la mano sin jugar (rendirse de inmediato).
    pub max_bet_then_abandon: bool,
    pub won: bool,
    pub surrendered: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Emotion {
    pub fascination: i32,
    pub despair: i32,
    disdain: i32,
    pub conservative_hands: u32,
    pub risky_hands: u32,
    pub streak_losses: u32,
    pub streak_wins: u32,
    pub honor_hand_pending: bool,
}

pub const DISDAIN_THRESHOLD: i32 = 100;

impl Default for Emotion {
    fn default() -> Self {
        Emotion { fascination: 20, despair: 0, disdain: 0, conservative_hands: 0, risky_hands: 0, streak_losses: 0, streak_wins: 0, honor_hand_pending: false }
    }
}

fn clamp(v: i32) -> i32 { v.clamp(0, 100) }

impl Emotion {
    pub fn apply(&mut self, e: EmotionEvent) {
        use EmotionEvent::*;
        let (f, d) = match e {
            Comeback => (12, 0), TenseHandWin => (8, 0), UnexpectedWin => (10, 0), SmartNegotiation => (10, 0),
            MeaninglessDuel => (-6, 0), Contempt => (-12, 0),
            SealWon => (0, 15), FundDeposit => (0, 8), TruthFound => (0, 12), IntentToLeave => (0, 10),
        };
        self.fascination = clamp(self.fascination + f);
        self.despair = clamp(self.despair + d);
    }

    /// El desden es oculto: solo se expone si hay Mano de Honor pendiente.
    pub fn disdain_level_hidden(&self) -> i32 { self.disdain }

    /// Registra una mano terminada: actualiza rachas, estilo y desden.
    /// El desden SOLO sube por patrones de autoboicot evidente; perder, apostar poco o rendirse no cuentan.
    pub fn record_hand(&mut self, r: HandRecord) {
        if r.won { self.streak_wins += 1; self.streak_losses = 0; } else { self.streak_losses += 1; self.streak_wins = 0; }
        if r.max_bet > 0 && r.bet * 2 >= r.max_bet { self.risky_hands += 1; } else { self.conservative_hands += 1; }
        if r.won && self.streak_losses == 0 && self.streak_wins == 1 { /* victoria suelta: sin efecto */ }
        let sabotage = r.hit_on_20_plus || r.max_bet_then_abandon;
        if sabotage { self.disdain = (self.disdain + 25).min(DISDAIN_THRESHOLD + 25); }
        else if self.disdain > 0 { self.disdain -= 5; }
        if self.disdain >= DISDAIN_THRESHOLD { self.honor_hand_pending = true; }
    }

    /// Termina la Mano de Honor: baja el desden (evento dramatico, no castigo).
    pub fn finish_honor_hand(&mut self) {
        self.honor_hand_pending = false;
        self.disdain = 20;
    }

    pub fn style(&self) -> &'static str {
        let total = self.conservative_hands + self.risky_hands;
        if total < 5 { "indefinido" } else if self.risky_hands * 100 / total >= 60 { "arriesgado" } else { "conservador" }
    }

    /// Multiplicador (en porcentaje) de la frecuencia de trampas segun emociones: 100 = base.
    pub fn cheat_frequency_pct(&self) -> i32 {
        100 + self.despair / 2 - (self.fascination / 4)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn values_are_clamped() {
        let mut e = Emotion::default();
        for _ in 0..20 { e.apply(EmotionEvent::Comeback); e.apply(EmotionEvent::SealWon); }
        assert_eq!((e.fascination, e.despair), (100, 100));
        for _ in 0..20 { e.apply(EmotionEvent::Contempt); }
        assert_eq!(e.fascination, 0);
    }

    #[test]
    fn can_be_high_together() {
        let mut e = Emotion::default();
        for _ in 0..8 { e.apply(EmotionEvent::UnexpectedWin); e.apply(EmotionEvent::TruthFound); }
        assert!(e.fascination > 80 && e.despair > 80);
    }

    #[test]
    fn losing_small_bets_and_surrender_never_raise_disdain() {
        let mut e = Emotion::default();
        for _ in 0..200 {
            e.record_hand(HandRecord { bet: 10, max_bet: 500, won: false, surrendered: true, ..Default::default() });
        }
        assert_eq!(e.disdain_level_hidden(), 0);
        assert!(!e.honor_hand_pending);
    }

    #[test]
    fn repeated_self_sabotage_triggers_honor_hand() {
        let mut e = Emotion::default();
        for _ in 0..3 { e.record_hand(HandRecord { bet: 500, max_bet: 500, hit_on_20_plus: true, ..Default::default() }); }
        assert!(!e.honor_hand_pending);
        e.record_hand(HandRecord { bet: 500, max_bet: 500, max_bet_then_abandon: true, ..Default::default() });
        assert!(e.honor_hand_pending);
        e.finish_honor_hand();
        assert!(!e.honor_hand_pending);
    }

    #[test]
    fn occasional_sabotage_decays() {
        let mut e = Emotion::default();
        e.record_hand(HandRecord { bet: 10, max_bet: 500, hit_on_20_plus: true, ..Default::default() });
        for _ in 0..10 { e.record_hand(HandRecord { bet: 10, max_bet: 500, won: true, ..Default::default() }); }
        assert_eq!(e.disdain_level_hidden(), 0);
    }

    #[test]
    fn style_memory() {
        let mut e = Emotion::default();
        for _ in 0..10 { e.record_hand(HandRecord { bet: 400, max_bet: 500, won: true, ..Default::default() }); }
        assert_eq!(e.style(), "arriesgado");
        let mut c = Emotion::default();
        for _ in 0..10 { c.record_hand(HandRecord { bet: 10, max_bet: 500, ..Default::default() }); }
        assert_eq!(c.style(), "conservador");
    }

    #[test]
    fn streaks() {
        let mut e = Emotion::default();
        for _ in 0..3 { e.record_hand(HandRecord { bet: 10, max_bet: 500, ..Default::default() }); }
        assert_eq!(e.streak_losses, 3);
        e.record_hand(HandRecord { bet: 10, max_bet: 500, won: true, ..Default::default() });
        assert_eq!((e.streak_losses, e.streak_wins), (0, 1));
    }

    #[test]
    fn serde_roundtrip() {
        let mut e = Emotion::default();
        e.apply(EmotionEvent::SealWon);
        let j = serde_json::to_string(&e).unwrap();
        assert_eq!(serde_json::from_str::<Emotion>(&j).unwrap(), e);
    }
}
