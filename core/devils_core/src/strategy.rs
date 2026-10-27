//! Estrategia basica (S17, DAS, rendicion tardia) usada por `devils_sim` y por los bots de prueba.
use crate::cards::Card;
use crate::hand::Hand;
use crate::table::Action;

fn pick(want: Action, fallback: Action, legal: &[Action]) -> Action {
    if legal.contains(&want) { want } else { fallback }
}

pub fn basic_strategy(hand: &Hand, up: Card, legal: &[Action]) -> Action {
    let u = up.rank.value(); // 2..=11
    let (v, soft) = crate::hand::total(&hand.cards);
    let hit = Action::Hit;
    let stand = Action::Stand;
    // Rendicion
    if legal.contains(&Action::Surrender) && !soft {
        if (v == 16 && (u == 9 || u == 10 || u == 11)) || (v == 15 && u == 10) { return Action::Surrender; }
    }
    // Pares
    if legal.contains(&Action::Split) {
        let p = hand.cards[0].rank.value();
        let split = match p {
            11 | 8 => true,
            9 => !matches!(u, 7 | 10 | 11),
            7 => u <= 7,
            6 => u <= 6,
            4 => matches!(u, 5 | 6),
            3 | 2 => u <= 7,
            _ => false,
        };
        if split { return Action::Split; }
    }
    if soft {
        return match v {
            19..=21 => if v == 19 && u == 6 { pick(Action::Double, stand, legal) } else { stand },
            18 => if (3..=6).contains(&u) { pick(Action::Double, stand, legal) } else if u <= 8 { stand } else { hit },
            17 => if (3..=6).contains(&u) { pick(Action::Double, hit, legal) } else { hit },
            15 | 16 => if (4..=6).contains(&u) { pick(Action::Double, hit, legal) } else { hit },
            13 | 14 => if (5..=6).contains(&u) { pick(Action::Double, hit, legal) } else { hit },
            _ => hit,
        };
    }
    match v {
        17..=21 => stand,
        13..=16 => if u <= 6 { stand } else { hit },
        12 => if (4..=6).contains(&u) { stand } else { hit },
        11 => pick(Action::Double, hit, legal),
        10 => if u <= 9 { pick(Action::Double, hit, legal) } else { hit },
        9 => if (3..=6).contains(&u) { pick(Action::Double, hit, legal) } else { hit },
        _ => hit,
    }
}
