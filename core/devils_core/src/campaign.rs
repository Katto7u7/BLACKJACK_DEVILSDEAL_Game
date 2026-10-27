//! Campana: 5 actos, duelo de Sello al mejor de 3 (empates se repiten) y 5 finales.
use serde::{Deserialize, Serialize};

pub const NORMAL_HANDS_PER_ACT: u32 = 6;
pub const LAST_ACT: u8 = 5;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Ending {
    /// 1: Regreso a la Vida
    ReturnToLife,
    /// 2: Una Eternidad Contigo
    EternityWithYou,
    /// 3: La Casa Gana (Pulso = 0)
    HouseWins,
    /// 4: El Pacto Roto (secreto: pruebas + fondo de retorno)
    BrokenPact,
    /// 5: El Nuevo Crupier (clausula)
    NewDealer,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum DuelHand { Win, Loss, Push }

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Duel { pub player: u8, pub dealer: u8, pub pushes: u8 }

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Phase { Normal, DuelDue, Duel }

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum CampaignEvent {
    DuelStarted { act: u8 },
    DuelHandResolved { player: u8, dealer: u8 },
    /// Sello ganado: el acto avanza.
    SealWon { act: u8 },
    /// Duelo perdido: fracaso critico (-1 Pulso). El duelo se repite.
    DuelLost { act: u8 },
    ActAdvanced { act: u8 },
    EndingReached(Ending),
}

/// Datos necesarios para decidir el final.
#[derive(Clone, Copy, Debug, Default)]
pub struct EndingInputs {
    pub pulse: u8,
    pub seals: u8,
    pub fascination: i32,
    pub despair: i32,
    pub fraud_proofs: u32,
    pub return_fund: i64,
    /// El jugador firmo la clausula final de Vespera (final 5).
    pub signed_clause: bool,
    /// El jugador acepto quedarse (final 2).
    pub chose_to_stay: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Campaign {
    pub act: u8,
    pub normal_hands: u32,
    pub phase: Phase,
    pub duel: Duel,
    pub ending: Option<Ending>,
    pub duels_lost: u32,
}

pub const BROKEN_PACT_PROOFS: u32 = 3;
pub const BROKEN_PACT_FUND: i64 = 500;

impl Default for Campaign {
    fn default() -> Self { Campaign { act: 1, normal_hands: 0, phase: Phase::Normal, duel: Duel::default(), ending: None, duels_lost: 0 } }
}

impl Campaign {
    /// Una mano normal terminada (no de duelo). Tras 6 manos el duelo queda pendiente.
    pub fn on_normal_hand(&mut self) -> Vec<CampaignEvent> {
        if self.ending.is_some() || self.phase != Phase::Normal { return vec![]; }
        self.normal_hands += 1;
        if self.normal_hands >= NORMAL_HANDS_PER_ACT { self.phase = Phase::DuelDue; }
        vec![]
    }

    pub fn start_duel(&mut self) -> Result<Vec<CampaignEvent>, String> {
        if self.phase != Phase::DuelDue { return Err("no hay duelo pendiente".into()); }
        self.phase = Phase::Duel;
        self.duel = Duel::default();
        Ok(vec![CampaignEvent::DuelStarted { act: self.act }])
    }

    /// Resuelve una mano del duelo. Empates se repiten sin puntuar. Devuelve (eventos, sello_ganado, fracaso_critico).
    pub fn on_duel_hand(&mut self, r: DuelHand, inputs: EndingInputs) -> (Vec<CampaignEvent>, bool, bool) {
        if self.phase != Phase::Duel { return (vec![], false, false); }
        let mut ev = vec![];
        match r {
            DuelHand::Win => self.duel.player += 1,
            DuelHand::Loss => self.duel.dealer += 1,
            DuelHand::Push => self.duel.pushes += 1,
        }
        ev.push(CampaignEvent::DuelHandResolved { player: self.duel.player, dealer: self.duel.dealer });
        if self.duel.player >= 2 {
            ev.push(CampaignEvent::SealWon { act: self.act });
            self.phase = Phase::Normal;
            self.normal_hands = 0;
            self.duel = Duel::default();
            if self.act >= LAST_ACT {
                let mut i = inputs;
                i.seals = i.seals.max(LAST_ACT);
                let e = Self::decide_ending(i);
                self.ending = Some(e);
                ev.push(CampaignEvent::EndingReached(e));
            } else {
                self.act += 1;
                ev.push(CampaignEvent::ActAdvanced { act: self.act });
            }
            return (ev, true, false);
        }
        if self.duel.dealer >= 2 {
            self.duels_lost += 1;
            ev.push(CampaignEvent::DuelLost { act: self.act });
            // El duelo se repite: se vuelve a "pendiente".
            self.phase = Phase::DuelDue;
            self.duel = Duel::default();
            return (ev, false, true);
        }
        (ev, false, false)
    }

    /// Pulso 0 en cualquier momento: final 3.
    pub fn on_pulse_zero(&mut self) -> Vec<CampaignEvent> {
        if self.ending.is_some() { return vec![]; }
        self.ending = Some(Ending::HouseWins);
        vec![CampaignEvent::EndingReached(Ending::HouseWins)]
    }

    /// Reglas de los finales (ninguno depende de un unico medidor ni de compras).
    pub fn decide_ending(i: EndingInputs) -> Ending {
        if i.pulse == 0 { return Ending::HouseWins; }
        if i.fraud_proofs >= BROKEN_PACT_PROOFS && i.return_fund >= BROKEN_PACT_FUND { return Ending::BrokenPact; }
        if i.signed_clause && i.seals >= LAST_ACT { return Ending::NewDealer; }
        if i.chose_to_stay && (i.fascination >= 60 || i.despair >= 60) { return Ending::EternityWithYou; }
        Ending::ReturnToLife
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ready(c: &mut Campaign) {
        for _ in 0..NORMAL_HANDS_PER_ACT { c.on_normal_hand(); }
        assert_eq!(c.phase, Phase::DuelDue);
        c.start_duel().unwrap();
    }

    #[test]
    fn duel_due_after_six_hands() {
        let mut c = Campaign::default();
        for _ in 0..5 { c.on_normal_hand(); }
        assert_eq!(c.phase, Phase::Normal);
        c.on_normal_hand();
        assert_eq!(c.phase, Phase::DuelDue);
        assert!(c.start_duel().is_ok());
        assert!(c.start_duel().is_err());
    }

    #[test]
    fn best_of_three_win_advances_act() {
        let mut c = Campaign::default();
        ready(&mut c);
        let (_, sealed, crit) = c.on_duel_hand(DuelHand::Win, EndingInputs::default());
        assert!(!sealed && !crit);
        let (ev, sealed, _) = c.on_duel_hand(DuelHand::Win, EndingInputs::default());
        assert!(sealed);
        assert_eq!(c.act, 2);
        assert!(ev.contains(&CampaignEvent::ActAdvanced { act: 2 }));
        assert_eq!(c.phase, Phase::Normal);
        assert_eq!(c.normal_hands, 0);
    }

    #[test]
    fn pushes_repeat_without_scoring() {
        let mut c = Campaign::default();
        ready(&mut c);
        for _ in 0..5 { c.on_duel_hand(DuelHand::Push, EndingInputs::default()); }
        assert_eq!((c.duel.player, c.duel.dealer), (0, 0));
        assert_eq!(c.phase, Phase::Duel);
    }

    #[test]
    fn losing_duel_is_critical_and_repeats() {
        let mut c = Campaign::default();
        ready(&mut c);
        c.on_duel_hand(DuelHand::Loss, EndingInputs::default());
        let (ev, sealed, crit) = c.on_duel_hand(DuelHand::Loss, EndingInputs::default());
        assert!(!sealed && crit);
        assert!(ev.contains(&CampaignEvent::DuelLost { act: 1 }));
        assert_eq!(c.act, 1);
        assert_eq!(c.phase, Phase::DuelDue);
        assert_eq!(c.duels_lost, 1);
        assert!(c.start_duel().is_ok());
    }

    #[test]
    fn win_lose_win_is_won() {
        let mut c = Campaign::default();
        ready(&mut c);
        c.on_duel_hand(DuelHand::Win, EndingInputs::default());
        c.on_duel_hand(DuelHand::Loss, EndingInputs::default());
        let (_, sealed, _) = c.on_duel_hand(DuelHand::Win, EndingInputs::default());
        assert!(sealed);
    }

    #[test]
    fn five_acts_reach_an_ending() {
        let mut c = Campaign::default();
        for a in 1..=5 {
            ready(&mut c);
            c.on_duel_hand(DuelHand::Win, EndingInputs::default());
            let (ev, _, _) = c.on_duel_hand(DuelHand::Win, EndingInputs { pulse: 3, ..Default::default() });
            if a == 5 { assert!(ev.iter().any(|e| matches!(e, CampaignEvent::EndingReached(_)))); }
        }
        assert_eq!(c.ending, Some(Ending::ReturnToLife));
        assert!(c.on_normal_hand().is_empty());
    }

    #[test]
    fn pulse_zero_is_house_wins() {
        let mut c = Campaign::default();
        assert_eq!(c.on_pulse_zero(), vec![CampaignEvent::EndingReached(Ending::HouseWins)]);
        assert_eq!(c.ending, Some(Ending::HouseWins));
        assert!(c.on_pulse_zero().is_empty());
    }

    #[test]
    fn endings_are_reachable_and_independent_of_one_meter() {
        let base = EndingInputs { pulse: 3, seals: 5, ..Default::default() };
        assert_eq!(Campaign::decide_ending(base), Ending::ReturnToLife);
        assert_eq!(Campaign::decide_ending(EndingInputs { pulse: 0, ..base }), Ending::HouseWins);
        assert_eq!(Campaign::decide_ending(EndingInputs { fraud_proofs: 3, return_fund: 500, ..base }), Ending::BrokenPact);
        assert_eq!(Campaign::decide_ending(EndingInputs { fraud_proofs: 3, return_fund: 100, ..base }), Ending::ReturnToLife);
        assert_eq!(Campaign::decide_ending(EndingInputs { signed_clause: true, ..base }), Ending::NewDealer);
        assert_eq!(Campaign::decide_ending(EndingInputs { chose_to_stay: true, fascination: 80, ..base }), Ending::EternityWithYou);
        assert_eq!(Campaign::decide_ending(EndingInputs { chose_to_stay: true, fascination: 10, despair: 10, ..base }), Ending::ReturnToLife);
    }

    #[test]
    fn serde_roundtrip() {
        let mut c = Campaign::default();
        ready(&mut c);
        let j = serde_json::to_string(&c).unwrap();
        assert_eq!(serde_json::from_str::<Campaign>(&j).unwrap(), c);
    }
}
