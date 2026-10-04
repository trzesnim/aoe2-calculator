import re

import requests
import streamlit as st

from lists import (
    elite,
    extra,
    units,
)


class Unit:
    def __init__(
        self,
        name: str,
        hp: int,
        p_attack=None,
        m_attack=None,
        rof: float = 0,
        armor: int = 0,
        pierce_armor: int = 0,
        attack_bonus=None,
        armor_class=None,
        boost_tech=None,
        elite=False,
    ):
        self._name = name
        self._hp = check_v(hp, name, elite)
        if p_attack:
            self._p_attack = check_v(p_attack, name, elite)
        else:
            self._p_attack = None
        if m_attack:
            self._m_attack = check_v(m_attack, name, elite)
        else:
            self._m_attack = None
        self._rof = check_v(rof, name, elite)
        self._armor = check_v(armor, name, elite)
        self._pierce_armor = check_v(pierce_armor, name, elite)
        self._attack_bonus = check_bonus(attack_bonus, elite)
        self._armor_class = check_class(armor_class)
        self._boost_tech = boost_tech
        self._elite = elite

    def __str__(self):
        return f"Name: {self.name}\nHP: {self.hp}\nPAttack: {self.p_attack}\nMAttack: {self.m_attack}\nROF: {self.rof}\nArmor: {self.armor}\nPierceArmor: {self.pierce_armor}\nAttack Bonus: {self.attack_bonus}\nArmor Class: {self.armor_class}\n"

    @property
    def name(self):
        return self._name

    @property
    def hp(self):
        return self._hp

    @property
    def p_attack(self):
        return self._p_attack

    @property
    def m_attack(self):
        return self._m_attack

    @property
    def rof(self):
        return self._rof

    @property
    def armor(self):
        return self._armor

    @property
    def pierce_armor(self):
        return self._pierce_armor

    @property
    def attack_bonus(self):
        return self._attack_bonus

    @property
    def armor_class(self):
        return self._armor_class

    @property
    def boost_tech(self):
        return self._boost_tech


def main():
    st.write("# Age of Empires 2 1v1 Battle Calculator")
    input1 = get_input(1)
    input2 = get_input(2)
    # st.write("\n", end="")
    content1, boost_techs1 = get_unit_info(input1)
    content2, boost_techs2 = get_unit_info(input2)
    unit1 = set_stats(content1, boost_techs1, 1)
    unit2 = set_stats(content2, boost_techs2, 2)
    st.write(unit1)
    st.write(unit2)
    st.write(compare(unit1, unit2))
    # st.write("\n", end="")


def get_unit_info(unit):
    unit = check_elite(unit)
    if unit == "Villager":
        unit = "Villager_(Age_of_Empires_II)"
    response = requests.get(
        f"https://ageofempires.fandom.com/api.php?action=query&prop=revisions&titles={unit}&rvprop=content&formatversion=2&format=json"
    )
    r = response.json()
    query = r["query"]
    if "'missing': True" in str(query):
        st.stop()
    content = query["pages"][0]["revisions"][0]["content"]
    if (
        "Disambig" in content or "disambig" in content or "ForNoLink" in content
    ) and "Bombard Cannon" not in content:
        unit = f"{unit}_(Age_of_Empires_II)"
        response = requests.get(
            f"https://ageofempires.fandom.com/api.php?action=query&prop=revisions&titles={unit}&rvprop=content&formatversion=2&format=json"
        )
        r = response.json()
        query = r["query"]
        content = query["pages"][0]["revisions"][0]["content"]
    pattern2 = r".+?Boosts\|Technologies(.+?){{Boosts\|.+"
    if match2 := re.search(pattern2, content, flags=re.DOTALL):
        boost_techs = match2.group(1)
    else:
        boost_techs = []
    return (
        re.sub(r"(<tabber>.+$)|(escription.+$)", "", content, flags=re.DOTALL),
        boost_techs,
    )


def check_v(v, n, elite):
    ages = {"1": "Dark Age", "2": "Feudal Age", "3": "Castle Age", "4": "Imperial Age"}
    pattern = r"(Dark Age|Feudal Age|Castle Age|Imperial Age)}} (\d)"
    try:
        if attack := dict(re.findall(pattern, v)):
            AGE_LABELS = {
                1: "Dark Age",
                2: "Feudal Age",
                3: "Castle Age",
                4: "Imperial Age",
            }
            input_age = int(
                st.segmented_control(
                    f"Select Age for {n}:",
                    options=[1, 2, 3, 4],
                    format_func=AGE_LABELS.get,
                    default=1,
                    key=f"age_select_{n}_{v}",
                )
            )
            age = ages.get(str(input_age))
            for i in range(3):
                if age not in attack:
                    age = ages.get(str(input_age - (i + 1)))
                else:
                    break
            return attack.get(age)
    except TypeError:
        return None
    clean_v = re.sub(r"\{\{tt\|([^|]+)\|.*?\}\}", r"\1", v)
    ptrn = r"(.+?)\s*,\s*(.+)"
    if match0 := re.search(ptrn, clean_v):
        stat = match0.group(2) if elite else match0.group(1)
    else:
        stat = clean_v
    if mtch := re.search(r"<br />(\d+) <small>", stat):
        stat = mtch.group(1)
    if match2 := re.search(r"(\d+).*?\([xX×\u00d7]\s*(\d+)\)", stat):
        stat = int(match2.group(1)) + int(match2.group(2))
    if num_match := re.search(r"([+-]?[\d.]+)", str(stat)):
        stat = num_match.group(1)
    return stat


def set_stats(content, techs, n):
    pattern = (
        r"(Name|HP|PAttack|MAttack|ROF|Armor|PierceArmor|AttackBonus|Class) = (.+)\n"
    )
    attack = dict(re.findall(pattern, content))
    if "ChampionIcon.jpg" in content:
        attack["Name"] = "Champion"
    elif "Twohanded aoe2DE.png" in content:
        attack["Name"] = "Two-Handed Swordsman"
    if "Xolotlicon" in content:
        attack["Name"] = "Xolotl Warrior"
        for k, v in attack.items():
            attack[k] = re.sub(r"<.+", "", v)
    el = False
    if attack.get("Name") in elite:
        el = st.checkbox(
            f"Elite {attack.get('Name')}?", key=f"check_{n}_elite_{attack.get('Name')}"
        )
        if el:
            attack["Name"] = f"Elite {attack.get('Name')}"
    return Unit(
        attack.get("Name"),
        attack.get("HP"),
        attack.get("PAttack"),
        attack.get("MAttack"),
        attack.get("ROF"),
        attack.get("Armor"),
        attack.get("PierceArmor"),
        attack.get("AttackBonus"),
        attack.get("Class"),
        techs,
        el,
    )


def get_input(n):
    unit = st.selectbox(f"Unit {n}", units, key=f"unit_select_{n}")
    u = unit.title()
    if u not in units:
        st.write("Enter a valid unit name")
    if u in extra:
        st.warning("Units with unique mechanics are not fully supported.")
        st.stop()
    return u


def check_elite(unit):
    response = requests.get(
        f"https://ageofempires.fandom.com/api.php?action=query&prop=revisions&titles=Elite_{unit}&rvprop=content&formatversion=2&format=json"
    )
    r = response.json()
    query = r["query"]
    if "'missing': True" in str(query):
        return unit
    else:
        if ask_elite(unit) == 1:
            return f"Elite {unit}"
        else:
            return unit


def ask_elite(unit):
    e = st.checkbox(f"Elite {unit}?")
    if e == True:
        return 1
    else:
        return 2


def check_bonus(bonus, elite):
    if not bonus:
        return None
    pattern = r"([+-]?\d+(?:\s*,\s*[+-]?\d+)?).*?vs\.?\s*.*?2class\|([^}|]+)"
    matches = re.findall(pattern, str(bonus))
    b = {}
    for nums, cls in matches:
        parts = [p.strip() for p in nums.split(",")]
        val = parts[1] if (elite and len(parts) > 1) else parts[0]
        b[cls.strip().title()] = int(val)
    return b


def check_class(bonus):
    if not bonus:
        return None
    pattern = r"2class\|([^}|]+)"
    b = list(re.findall(pattern, bonus))
    for i, k in enumerate(b):
        if k == "Archer":
            b[i] = "Archers"
        if k == "Gunpowder unit":
            b[i] = "Gunpowder Units"
        if k == "Unique unit":
            b[i] = "Unique Units"
    b = [i.title() for i in b]
    return b


def compare(unit1, unit2):
    bonus1 = bonus_dmg(unit1, unit2)
    bonus2 = bonus_dmg(unit2, unit1)
    ab1, pab1, mab1, rb1, hpb1 = ask_upgrades(unit1, unit2, 1)
    # st.write("\n", end="")
    ab2, pab2, mab2, rb2, hpb2 = ask_upgrades(unit2, unit1, 2)
    # st.write("\n", end="")
    if unit1.p_attack:
        attack1 = (int(unit1.p_attack) + int(ab1)) - (
            int(unit2.pierce_armor) + int(pab2)
        )
    elif unit1.m_attack:
        attack1 = (int(unit1.m_attack) + int(ab1)) - (int(unit2.armor) + int(mab2))
    else:
        return f"{unit1.name} does not attack"
    attack1 = max(attack1, 1)
    attack1 = attack1 + int(bonus1)
    attack1 = max(1, attack1)
    if unit2.p_attack:
        attack2 = (int(unit2.p_attack) + int(ab2)) - (
            int(unit1.pierce_armor) + int(pab1)
        )
    elif unit2.m_attack:
        attack2 = (int(unit2.m_attack) + int(ab2)) - (int(unit1.armor) + int(mab1))
    else:
        return f"{unit2.name} does not attack"
    attack2 = max(attack2, 1)
    attack2 = attack2 + int(bonus2)
    attack2 = max(1, attack2)
    hp1 = int(unit1.hp) + hpb1
    time1 = -(float(unit1.rof) * rb1)
    hits1 = 0
    hp2 = int(unit2.hp) + hpb2
    time2 = -(float(unit2.rof) * rb2)
    hits2 = 0
    # 2 attacks 1
    while hp1 > 0:
        hp1 = hp1 - attack2
        time2 = time2 + (float(unit2.rof) * rb2)
        hits2 += 1
    # 1 attacks 2
    while hp2 > 0:
        hp2 = hp2 - attack1
        time1 = time1 + (float(unit1.rof) * rb1)
        hits1 += 1
    text = f"{unit1.name} takes {hits1} hits and {time1:.2f} seconds to kill {unit2.name}\n\n{unit2.name} takes {hits2} hits and {time2:.2f} seconds to kill {unit1.name}"
    if time1 < time2:
        return f"{text}\n\n{unit1.name} wins 1v1"
    elif time1 > time2:
        return f"{text}\n\n{unit2.name} wins 1v1"
    else:
        return f"{text}\n\nBoth units takes the same time to kill each other"


def bonus_dmg(u1, u2):
    if not u2.armor_class or not u1.attack_bonus:
        return 0
    bonus = 0
    for ac in u2.armor_class:
        if ac in u1.attack_bonus:
            bonus = bonus + int(u1.attack_bonus[ac])
    return bonus


def ask_upgrades(unit, u2, n):
    attack_bonus = 0
    parmor_bonus = 0
    marmor_bonus = 0
    rof_bonus = 1
    hp_bonus = 0
    if "Fletching" in unit.boost_tech:
        st.write(f"{unit.name} attack upgrades:")
        ATTACK_LABELS = {
            0: "None",
            1: "Fletching",
            2: "Bodkin Arrow",
            3: "Bracer",
        }
        attack_bonus = int(
            st.segmented_control(
                "Attack Bonus",
                options=[0, 1, 2, 3],
                format_func=ATTACK_LABELS.get,
                default=0,
                key=f"pierce_attack_bonus_{n}_{unit.name}",
            )
        )
    elif "Forging" in unit.boost_tech:
        st.write(f"{unit.name} attack upgrades:")
        ATTACK_LABELS = {
            0: "None",
            1: "Forging",
            2: "Iron Casting",
            3: "Blast Furnace",
        }
        attack_bonus = int(
            st.segmented_control(
                "Attack Bonus",
                options=[0, 1, 2, 3],
                format_func=ATTACK_LABELS.get,
                default=0,
                key=f"melee_attack_bonus_{n}_{unit.name}",
            )
        )
        if attack_bonus == 3:
            attack_bonus = 4
    if "Padded Archer Armor" in unit.boost_tech:
        st.write(f"{unit.name} armor upgrades:")
        ARMOR_LABELS = {
            0: "None",
            1: "Padded Archer Armor",
            2: "Leather Archer Armor",
            3: "Ring Archer Armor",
        }
        armor_bonus = int(
            st.segmented_control(
                "Armor Bonus",
                options=[0, 1, 2, 3],
                format_func=ARMOR_LABELS.get,
                default=0,
                key=f"archer_armor_bonus_{n}_{unit.name}",
            )
        )
        if armor_bonus == 3:
            parmor_bonus = armor_bonus + 1
        else:
            parmor_bonus = armor_bonus
        marmor_bonus = armor_bonus
    if "Scale Barding Armor" in unit.boost_tech:
        st.write(f"{unit.name} armor upgrades:")
        ARMOR_LABELS = {
            0: "None",
            1: "Scale Barding Armor",
            2: "Chain Barding Armor",
            3: "Plate Barding Armor",
        }
        armor_bonus = int(
            st.segmented_control(
                "Armor Bonus",
                options=[0, 1, 2, 3],
                format_func=ARMOR_LABELS.get,
                default=0,
                key=f"cav_armor_bonus_{n}_{unit.name}",
            )
        )
        if armor_bonus == 3:
            parmor_bonus = armor_bonus + 1
        else:
            parmor_bonus = armor_bonus
        marmor_bonus = armor_bonus
    if "Scale Mail Armor" in unit.boost_tech:
        st.write(f"{unit.name} armor upgrades:")
        ARMOR_LABELS = {
            0: "None",
            1: "Scale Mail Armor",
            2: "Chain Mail Armor",
            3: "Plate Mail Armor",
        }
        armor_bonus = int(
            st.segmented_control(
                "Armor Bonus",
                options=[0, 1, 2, 3],
                format_func=ARMOR_LABELS.get,
                default=0,
                key=f"infantry_armor_bonus_{n}_{unit.name}",
            )
        )
        if armor_bonus == 3:
            parmor_bonus = armor_bonus + 1
        else:
            parmor_bonus = armor_bonus
        marmor_bonus = armor_bonus
    if "Chemistry" in unit.boost_tech:
        chem = st.checkbox("Chemistry?", key=f"chemistry_{n}_{unit.name}")
        if chem == True:
            attack_bonus += 1
    if (
        "Thumb Ring" in unit.boost_tech
        and "Skirmisher" not in unit.name
        and "Genitour" not in unit.name
    ):
        thumb = st.checkbox("Thumb Ring?", key=f"thumb_ring_{n}_{unit.name}")
        if thumb == True:
            if "Cavalry Archer" in unit.name:
                rof_bonus = 0.9
            else:
                rof_bonus = 0.85
    if "Bloodlines" in unit.boost_tech:
        blood = st.checkbox("Bloodlines?", key=f"bloodlines_{n}_{unit.name}")
        if blood == True:
            hp_bonus = 20
    if "Parthian Tactics" in unit.boost_tech:
        parth = st.checkbox(
            "Parthian Tactics?", key=f"parthian_tactics_{n}_{unit.name}"
        )
        if parth == True:
            marmor_bonus += 1
            parmor_bonus += 1
            if "Spearmen" in u2.armor_class:
                attack_bonus += 2
    if "Gambesons" in unit.boost_tech:
        gamb = st.checkbox("Gambesons?", key=f"gambesons_{n}_{unit.name}")
        if gamb == True:
            parmor_bonus += 1
    if "Cranequins" in unit.boost_tech:
        cra = st.checkbox("Cranequins?", key=f"cranequins_{n}_{unit.name}")
        if cra == True and "Infantry" in u2.armor_class:
            attack_bonus += 2
    if "Villager" in unit.name:
        loom = st.checkbox("Loom?", key=f"loom_{n}_{unit.name}")
        if loom == True:
            marmor_bonus += 1
            parmor_bonus += 2
            hp_bonus += 15
    return attack_bonus, parmor_bonus, marmor_bonus, rof_bonus, hp_bonus


if __name__ == "__main__":
    main()
