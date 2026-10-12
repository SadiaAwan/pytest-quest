"""Level 09: quest states, errors, rewards and deadlines."""

import pytest

from dungeon.hero import Hero
from dungeon.quests import Quest, QuestError, QuestLog, QuestState


def test_goblin_quest_starts_available():
    log = QuestLog()
    quest = Quest("Goblin treasure", ["Find key", "Open chest"])

    log.offer(quest)

    assert log.get(quest.title) is quest
    assert quest.state is QuestState.AVAILABLE
    assert quest.done == set()
    assert quest.remaining == ["Find key", "Open chest"]
    assert log.active() == []
    assert log.max_active == 3


@pytest.mark.parametrize("max_active", [0, -1])
def test_log_rejects_invalid_capacity(max_active):
    with pytest.raises(ValueError, match="max_active must be at least 1"):
        QuestLog(max_active=max_active)


def test_offer_rejects_duplicate_title():
    log = QuestLog()
    original = Quest("Treasure", ["Find key"])
    log.offer(original)

    with pytest.raises(QuestError, match="already in the log"):
        log.offer(Quest("Treasure", ["Open chest"]))

    assert log.get("Treasure") is original


def test_offer_rejects_empty_objectives():
    log = QuestLog()

    with pytest.raises(QuestError, match="at least one objective"):
        log.offer(Quest("Empty", []))

    with pytest.raises(QuestError, match="unknown quest"):
        log.get("Empty")


def test_get_rejects_unknown_title():
    log = QuestLog()

    with pytest.raises(QuestError, match="unknown quest"):
        log.get("Missing")


def test_accept_allows_exact_required_level():
    log = QuestLog()
    hero = Hero("Sadia", level=2)
    quest = Quest("Treasure", ["Find key"], required_level=2)
    log.offer(quest)

    result = log.accept(hero, quest.title)

    assert result is quest
    assert quest.state is QuestState.ACTIVE
    assert log.active() == [quest]


def test_accept_rejects_hero_below_required_level():
    log = QuestLog()
    hero = Hero("Sadia", level=1)
    quest = Quest("Treasure", ["Find key"], required_level=2)
    log.offer(quest)

    with pytest.raises(QuestError, match="must be level 2"):
        log.accept(hero, quest.title)

    assert quest.state is QuestState.AVAILABLE
    assert log.active() == []


@pytest.mark.parametrize(
    "state",
    [
        QuestState.ACTIVE,
        QuestState.COMPLETED,
        QuestState.TURNED_IN,
        QuestState.FAILED,
    ],
)
def test_accept_rejects_unavailable_quest(state):
    log = QuestLog()
    hero = Hero("Sadia")
    quest = Quest("Treasure", ["Find key"], state=state)
    log.offer(quest)

    with pytest.raises(QuestError):
        log.accept(hero, quest.title)

    assert quest.state is state


def test_accept_rejects_when_capacity_is_reached():
    log = QuestLog(max_active=1)
    hero = Hero("Sadia")
    first = Quest("First", ["Find key"])
    second = Quest("Second", ["Open chest"])
    log.offer(first)
    log.offer(second)
    log.accept(hero, first.title)

    with pytest.raises(QuestError, match="active quests"):
        log.accept(hero, second.title)

    assert first.state is QuestState.ACTIVE
    assert second.state is QuestState.AVAILABLE
    assert log.active() == [first]


def test_objectives_complete_only_after_last_objective():
    log = QuestLog()
    hero = Hero("Sadia")
    quest = Quest("Treasure", ["Find key", "Open chest", "Take gold"])
    log.offer(quest)
    log.accept(hero, quest.title)

    assert log.complete_objective(quest.title, "Open chest") is False
    assert quest.state is QuestState.ACTIVE
    assert quest.done == {"Open chest"}
    assert quest.remaining == ["Find key", "Take gold"]

    assert log.complete_objective(quest.title, "Open chest") is False
    assert quest.done == {"Open chest"}

    assert log.complete_objective(quest.title, "Find key") is False
    assert quest.remaining == ["Take gold"]

    assert log.complete_objective(quest.title, "Take gold") is True
    assert quest.state is QuestState.COMPLETED
    assert quest.remaining == []
    assert quest.done == {"Find key", "Open chest", "Take gold"}
    assert log.active() == []


@pytest.mark.parametrize(
    "state",
    [
        QuestState.AVAILABLE,
        QuestState.COMPLETED,
        QuestState.TURNED_IN,
        QuestState.FAILED,
    ],
)
def test_complete_objective_rejects_inactive_quest(state):
    log = QuestLog()
    quest = Quest("Treasure", ["Find key"], state=state)
    log.offer(quest)

    with pytest.raises(QuestError, match="not active"):
        log.complete_objective(quest.title, "Find key")

    assert quest.state is state
    assert quest.done == set()


def test_complete_objective_rejects_unknown_objective():
    log = QuestLog()
    quest = Quest("Treasure", ["Find key"])
    log.offer(quest)
    log.accept(Hero("Sadia"), quest.title)

    with pytest.raises(QuestError, match="not part of"):
        log.complete_objective(quest.title, "Fly")

    assert quest.state is QuestState.ACTIVE
    assert quest.done == set()
    assert quest.remaining == ["Find key"]


def test_turn_in_gives_rewards_once():
    log = QuestLog()
    hero = Hero("Sadia", gold=10, xp=90)
    quest = Quest(
        "Treasure",
        ["Find key"],
        reward_xp=120,
        reward_gold=25,
    )
    log.offer(quest)
    log.accept(hero, quest.title)
    log.complete_objective(quest.title, "Find key")

    levels = log.turn_in(hero, quest.title)

    assert levels == 2
    assert hero.level == 3
    assert hero.xp == 10
    assert hero.gold == 35
    assert quest.state is QuestState.TURNED_IN

    with pytest.raises(QuestError, match="not completed"):
        log.turn_in(hero, quest.title)

    assert (hero.level, hero.xp, hero.gold) == (3, 10, 35)


@pytest.mark.parametrize(
    "state",
    [QuestState.AVAILABLE, QuestState.ACTIVE, QuestState.FAILED],
)
def test_turn_in_rejects_uncompleted_quest_without_rewards(state):
    log = QuestLog()
    hero = Hero("Sadia", gold=10, xp=20)
    quest = Quest(
        "Treasure",
        ["Find key"],
        reward_xp=100,
        reward_gold=25,
        state=state,
    )
    log.offer(quest)

    with pytest.raises(QuestError, match="not completed"):
        log.turn_in(hero, quest.title)

    assert (hero.level, hero.xp, hero.gold) == (1, 20, 10)
    assert quest.state is state


def test_abandon_clears_progress_and_allows_restart():
    log = QuestLog()
    hero = Hero("Sadia")
    quest = Quest("Treasure", ["Find key", "Open chest"])
    log.offer(quest)
    log.accept(hero, quest.title)
    log.complete_objective(quest.title, "Find key")

    assert log.abandon(quest.title) is None
    assert quest.state is QuestState.AVAILABLE
    assert quest.done == set()
    assert quest.remaining == ["Find key", "Open chest"]
    assert log.active() == []

    log.accept(hero, quest.title)

    assert log.complete_objective(quest.title, "Open chest") is False
    assert quest.remaining == ["Find key"]
    assert quest.state is QuestState.ACTIVE


@pytest.mark.parametrize(
    "state",
    [
        QuestState.AVAILABLE,
        QuestState.COMPLETED,
        QuestState.TURNED_IN,
        QuestState.FAILED,
    ],
)
def test_abandon_rejects_inactive_quest(state):
    log = QuestLog()
    quest = Quest("Treasure", ["Find key"], state=state)
    log.offer(quest)

    with pytest.raises(QuestError, match="not active"):
        log.abandon(quest.title)

    assert quest.state is state


@pytest.mark.parametrize("turns", [0, -1])
def test_tick_rejects_nonpositive_turns(turns):
    log = QuestLog()
    quest = Quest("Timed", ["Find key"], deadline=3)
    log.offer(quest)
    log.accept(Hero("Sadia"), quest.title)

    with pytest.raises(ValueError, match="time only moves forward"):
        log.tick(turns)

    assert quest.deadline == 3
    assert quest.state is QuestState.ACTIVE


def test_tick_decreases_deadline_without_failing_early():
    log = QuestLog()
    quest = Quest("Timed", ["Find key"], deadline=3)
    log.offer(quest)
    log.accept(Hero("Sadia"), quest.title)

    assert log.tick() == []
    assert quest.deadline == 2
    assert quest.state is QuestState.ACTIVE


@pytest.mark.parametrize("turns", [2, 3])
def test_tick_fails_at_zero_or_below(turns):
    log = QuestLog()
    quest = Quest("Timed", ["Find key"], deadline=2)
    log.offer(quest)
    log.accept(Hero("Sadia"), quest.title)

    assert log.tick(turns) == [quest]
    assert quest.deadline == 2 - turns
    assert quest.state is QuestState.FAILED
    assert log.active() == []

    assert log.tick() == []
    assert quest.deadline == 2 - turns


def test_tick_ignores_active_quest_without_deadline():
    log = QuestLog()
    quest = Quest("Untimed", ["Find key"])
    log.offer(quest)
    log.accept(Hero("Sadia"), quest.title)

    assert log.tick(10) == []
    assert quest.deadline is None
    assert quest.state is QuestState.ACTIVE


@pytest.mark.parametrize(
    "state",
    [
        QuestState.AVAILABLE,
        QuestState.COMPLETED,
        QuestState.TURNED_IN,
        QuestState.FAILED,
    ],
)
def test_tick_ignores_inactive_quests(state):
    log = QuestLog()
    quest = Quest("Inactive", ["Find key"], deadline=2, state=state)
    log.offer(quest)

    assert log.tick(10) == []
    assert quest.deadline == 2
    assert quest.state is state


def test_empty_log_summary_has_zero_for_every_state():
    log = QuestLog()

    assert log.summary() == {
        "available": 0,
        "active": 0,
        "completed": 0,
        "turned_in": 0,
        "failed": 0,
    }


def test_summary_counts_quests_in_every_state():
    log = QuestLog()

    for state in QuestState:
        log.offer(Quest(state.value, ["Find key"], state=state))

    log.offer(Quest("Another available", ["Open chest"]))

    assert log.summary() == {
        "available": 2,
        "active": 1,
        "completed": 1,
        "turned_in": 1,
        "failed": 1,
    }