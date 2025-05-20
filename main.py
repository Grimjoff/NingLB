import sqlite3
import requests


class LeaderBoard:
    def __init__(self):
        self.uids = {
            0: "704913795",
            1: "605981325",
            2: "831017549",
            3: "603566672",
            4: "702781917",
            5: "604789363",
            6: "715769498",
            7: "804214404",
            8: "849298881",
            9: "602595332",
            10: "808434791"
        }
        self.weapons = {
            1455107995: "Lost Prayer",
            807607555: "Skyward Atlas",
            359484419: "Tulaytullah's",
            1163263227: "The Widsith",
            693354267: "Memory of Dust"
        }

    def get_uid(self, number):
        return self.uids.get(number)

    def get_weapon_name(self, name_hash):
        return self.weapons.get(name_hash, "Unknown Weapon")

    def create_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS NingguangLB (
                UID TEXT PRIMARY KEY,
                USERNAME TEXT,
                DAMAGE INTEGER,
                CV TEXT,
                ATTACK INTEGER,
                WEAPON TEXT
            )
        ''')

    def lb(self):
        conn = sqlite3.connect('NingguangLeaderboard')
        c = conn.cursor()
        self.create_table(c)

        for j in range(10):
            uid = self.get_uid(j)
            if uid is None:
                print("done")
                break

            try:
                print("getting data")
                getData = requests.get(f"https://enka.network/api/uid/{uid}")
                if getData.status_code != 200:
                    print(f"API returned status {getData.status_code} for UID {uid}")
                    continue
                data = getData.json()
            except Exception as e:
                print(f"Error fetching data for UID {uid}: {e}")
                continue

            nickname = data.get("playerInfo", {}).get("nickname", "Unknown")
            avatar_list = data.get("avatarInfoList", [])
            show_avatar_list = data.get("playerInfo", {}).get("showAvatarInfoList", [])

            if not avatar_list or not show_avatar_list:
                continue

            for show_avatar in show_avatar_list:
                if show_avatar.get("avatarId") != 10000027:  # Ningguang ID
                    continue

                avatar_info = next((a for a in avatar_list if a.get("avatarId") == 10000027), None)
                if not avatar_info:
                    continue

                equips = avatar_info.get("equipList", [])
                if len(equips) != 6:
                    continue

                # Artifact set counters
                set_counts = {
                    147298547: 0,    # WT
                    1751039235: 0,   # NO
                    1438974835: 0,   # RB
                    4144069251: 0,   # SR
                    2276480763: 0    # EoSF
                }

                ca_bonus = 1.0
                burst_bonus = 1.0
                weapon_cv = 0.0

                for item in equips[:5]:  # first 5 are artifacts
                    set_id = item["flat"].get("setNameTextMapHash")
                    if set_id in set_counts:
                        set_counts[set_id] += 1

                if set_counts[147298547] >= 4:
                    ca_bonus = 1.35
                if set_counts[1751039235] >= 2:
                    burst_bonus = 1.2
                if set_counts[1438974835] >= 4:
                    ca_bonus = 1.4
                if set_counts[4144069251] >= 4:
                    ca_bonus = 1.5
                if set_counts[2276480763] >= 4:
                    er = avatar_info["fightPropMap"].get("23", 0)
                    burst_bonus = 1 + (er * 0.25)

                weapon = equips[5]
                weapon_stats = weapon["flat"].get("weaponStats", [])
                if len(weapon_stats) > 1:
                    append_id = weapon_stats[1].get("appendPropId")
                    stat_value = weapon_stats[1].get("statValue", 0)
                    if append_id == "FIGHT_PROP_CRITICAL":
                        weapon_cv = 2 * stat_value / 100
                    elif append_id == "FIGHT_PROP_CRITICAL_HURT":
                        weapon_cv = stat_value / 100

                weapon_name = self.get_weapon_name(weapon["flat"].get("nameTextMapHash"))

                props = avatar_info["fightPropMap"]
                crit_rate = props.get("20", 0)
                crit_dmg = props.get("22", 0)
                atk_base = props.get("4", 0)
                atk_percent = props.get("6", 0)
                atk_flat = props.get("5", 0)
                geo_bonus = props.get("45", 0)
                total_atk = atk_base * (1 + atk_percent) + atk_flat

                total_cv = round(100 * (crit_dmg + 2 * crit_rate - weapon_cv - 0.6), 1)
                dmg_multiplier = (1 + crit_rate * crit_dmg)
                enemy_reduction = 0.5 * 0.9

                avg_skill_no_buff = total_atk * 4.896 * (1 + geo_bonus) * dmg_multiplier * enemy_reduction
                geo_bonus += 0.12  # additional geo bonus from talents or resonance
                avg_skill_buff = total_atk * 4.896 * (1 + geo_bonus) * dmg_multiplier * enemy_reduction
                avg_burst = 12 * total_atk * 1.8479 * (1 + geo_bonus) * dmg_multiplier * burst_bonus * enemy_reduction
                avg_ca = total_atk * 3.1334 * (1 + geo_bonus) * dmg_multiplier * ca_bonus * enemy_reduction
                avg_star_jade = 7 * total_atk * 0.8928 * (1 + geo_bonus) * dmg_multiplier * ca_bonus * enemy_reduction

                total_dmg = int(avg_skill_no_buff + avg_skill_buff + avg_burst + avg_ca + avg_star_jade)

                c.execute("SELECT UID FROM NingguangLB WHERE UID = ?", (uid,))
                exists = c.fetchone()

                if exists:
                    c.execute('''
                        UPDATE NingguangLB
                        SET DAMAGE = ?, CV = ?, ATTACK = ?, WEAPON = ?
                        WHERE UID = ?
                    ''', (total_dmg, f"{total_cv}", int(total_atk), weapon_name, uid))
                else:
                    c.execute('''
                        INSERT OR IGNORE INTO NingguangLB (UID, USERNAME, DAMAGE, CV, ATTACK, WEAPON)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (uid, nickname, total_dmg, f"{total_cv}", int(total_atk), weapon_name))

                conn.commit()

        conn.close()


# Run the leaderboard calculation
if __name__ == "__main__":
    leaderboard = LeaderBoard()
    leaderboard.lb()
