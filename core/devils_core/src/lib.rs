//! Nucleo de reglas de Blackjack: Devil's Deal. Puro Rust, sin Godot.
pub mod campaign;
pub mod cards;
pub mod cheats;
pub mod contracts;
pub mod economy;
pub mod emotion;
pub mod game;
pub mod hand;
pub mod memory_cards;
pub mod rules;
pub mod shoe;
pub mod side_bets;
pub mod strategy;
pub mod table;

pub use cards::{Card, Rank, Suit};
pub use hand::{Hand, HandStatus, Outcome};
pub use rules::TableRules;
pub use shoe::Shoe;
pub use table::{Action, Event, Hint, Phase, Table, Target};
