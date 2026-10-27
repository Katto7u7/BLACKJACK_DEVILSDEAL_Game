//! Cartas de Memoria (comodines): 3 espacios equipables, 1 activacion por mano, usos limitados.
//! Reglas de diseno: nunca retroceden un resultado ya aceptado; ninguna convierte automaticamente una derrota
//! importante en victoria; nunca son obligatorias; Mesa Sellada las desactiva.
use serde::{Deserialize, Serialize};

pub const SLOTS: usize = 3;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MemoryCard {
    /// Cambia la ultima carta pedida por otra (justo tras pedir, antes de decidir).
    SecondChance,
    /// Ver la siguiente carta del zapato.
    EyeOfDestiny,
    /// Cancela el contrato activo sin penalizacion.
    ContractBreaker,
    /// Evita perder el ultimo punto de Pulso (una vez).
    LastHeartbeat,
    /// Esta ronda Vespera no puede hacer trampa (se usa antes de repartir).
    InfernalSilence,
    /// Revela si hay trampa en la ronda actual (sin decir cual).
    TruthHurts,
    /// Si pierdes esta mano, recuperas la mitad de la apuesta.
    TwinChips,
}

impl MemoryCard {
    pub const ALL: [MemoryCard; 7] = [MemoryCard::SecondChance, MemoryCard::EyeOfDestiny, MemoryCard::ContractBreaker, MemoryCard::LastHeartbeat,
        MemoryCard::InfernalSilence, MemoryCard::TruthHurts, MemoryCard::TwinChips];
    /// Usos maximos por acto (las potentes son limitadas).
    pub fn uses_per_act(self) -> u8 {
        match self {
            MemoryCard::SecondChance | MemoryCard::LastHeartbeat | MemoryCard::ContractBreaker => 1,
            MemoryCard::EyeOfDestiny | MemoryCard::TruthHurts | MemoryCard::InfernalSilence => 2,
            MemoryCard::TwinChips => 2,
        }
    }
    /// Solo se puede usar con la ronda aun sin repartir.
    pub fn before_deal_only(self) -> bool { self == MemoryCard::InfernalSilence }
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MemoryDeck {
    pub unlocked: Vec<MemoryCard>,
    pub equipped: Vec<MemoryCard>,
    uses: Vec<(MemoryCard, u8)>,
    used_this_hand: bool,
}

impl MemoryDeck {
    pub fn unlock(&mut self, c: MemoryCard) { if !self.unlocked.contains(&c) { self.unlocked.push(c); } }

    pub fn equip(&mut self, c: MemoryCard) -> Result<(), String> {
        if !self.unlocked.contains(&c) { return Err("carta no desbloqueada".into()); }
        if self.equipped.contains(&c) { return Err("ya equipada".into()); }
        if self.equipped.len() >= SLOTS { return Err("sin espacios".into()); }
        self.equipped.push(c);
        Ok(())
    }

    pub fn unequip(&mut self, c: MemoryCard) { self.equipped.retain(|x| *x != c); }

    pub fn new_act(&mut self) { self.uses.clear(); }
    pub fn new_hand(&mut self) { self.used_this_hand = false; }

    pub fn uses_left(&self, c: MemoryCard) -> u8 {
        c.uses_per_act().saturating_sub(self.uses.iter().find(|u| u.0 == c).map_or(0, |u| u.1))
    }

    /// Comprueba y consume un uso. `disabled` = Mesa Sellada; `dealt` = ya se repartio la ronda.
    pub fn activate(&mut self, c: MemoryCard, disabled: bool, dealt: bool) -> Result<(), String> {
        if disabled { return Err("Mesa Sellada: sin memorias".into()); }
        if !self.equipped.contains(&c) { return Err("carta no equipada".into()); }
        if self.used_this_hand { return Err("una activacion por mano".into()); }
        if self.uses_left(c) == 0 { return Err("sin usos este acto".into()); }
        if c.before_deal_only() && dealt { return Err("solo antes de repartir".into()); }
        if !c.before_deal_only() && !dealt { return Err("solo con la ronda en curso".into()); }
        match self.uses.iter_mut().find(|u| u.0 == c) { Some(u) => u.1 += 1, None => self.uses.push((c, 1)) }
        self.used_this_hand = true;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn deck() -> MemoryDeck {
        let mut d = MemoryDeck::default();
        for c in MemoryCard::ALL { d.unlock(c); }
        d
    }

    #[test]
    fn three_slots_only() {
        let mut d = deck();
        d.equip(MemoryCard::SecondChance).unwrap();
        d.equip(MemoryCard::EyeOfDestiny).unwrap();
        d.equip(MemoryCard::TwinChips).unwrap();
        assert!(d.equip(MemoryCard::TruthHurts).is_err());
        assert!(d.equip(MemoryCard::TwinChips).is_err());
        d.unequip(MemoryCard::TwinChips);
        assert!(d.equip(MemoryCard::TruthHurts).is_ok());
    }

    #[test]
    fn cannot_equip_locked() {
        let mut d = MemoryDeck::default();
        assert!(d.equip(MemoryCard::SecondChance).is_err());
    }

    #[test]
    fn one_activation_per_hand() {
        let mut d = deck();
        d.equip(MemoryCard::EyeOfDestiny).unwrap();
        d.equip(MemoryCard::TruthHurts).unwrap();
        d.activate(MemoryCard::EyeOfDestiny, false, true).unwrap();
        assert!(d.activate(MemoryCard::TruthHurts, false, true).is_err());
        d.new_hand();
        assert!(d.activate(MemoryCard::TruthHurts, false, true).is_ok());
    }

    #[test]
    fn limited_uses_per_act_reset_on_new_act() {
        let mut d = deck();
        d.equip(MemoryCard::SecondChance).unwrap();
        d.activate(MemoryCard::SecondChance, false, true).unwrap();
        d.new_hand();
        assert!(d.activate(MemoryCard::SecondChance, false, true).is_err());
        d.new_act();
        assert!(d.activate(MemoryCard::SecondChance, false, true).is_ok());
    }

    #[test]
    fn sealed_table_disables_everything() {
        let mut d = deck();
        d.equip(MemoryCard::EyeOfDestiny).unwrap();
        assert!(d.activate(MemoryCard::EyeOfDestiny, true, true).is_err());
        assert_eq!(d.uses_left(MemoryCard::EyeOfDestiny), 2);
    }

    #[test]
    fn timing_windows() {
        let mut d = deck();
        d.equip(MemoryCard::InfernalSilence).unwrap();
        d.equip(MemoryCard::EyeOfDestiny).unwrap();
        assert!(d.activate(MemoryCard::InfernalSilence, false, true).is_err());
        assert!(d.activate(MemoryCard::EyeOfDestiny, false, false).is_err());
        assert!(d.activate(MemoryCard::InfernalSilence, false, false).is_ok());
    }

    #[test]
    fn not_equipped_cannot_be_used() {
        let mut d = deck();
        assert!(d.activate(MemoryCard::TwinChips, false, true).is_err());
    }
}
