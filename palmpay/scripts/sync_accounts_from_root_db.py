"""Copy accounts + palm gallery from root app.db into palmpay app.db."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "data" / "store" / "app.db"
DST = ROOT / "data" / "store" / "app.db"


def cols(con: sqlite3.Connection, table: str) -> list[str]:
    return [c[1] for c in con.execute(f"pragma table_info({table})")]


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing source DB: {SRC}")
    if not DST.is_file():
        raise SystemExit(f"Missing dest DB: {DST}")

    src = sqlite3.connect(str(SRC))
    dst = sqlite3.connect(str(DST))
    src.row_factory = sqlite3.Row
    dst.row_factory = sqlite3.Row

    src_acc_cols = cols(src, "accounts")
    dst_acc_cols = cols(dst, "accounts")
    shared_acc = [c for c in src_acc_cols if c in dst_acc_cols and c != "id"]

    print(f"Source accounts: {src.execute('select count(*) from accounts').fetchone()[0]}")
    print(f"Dest accounts before: {dst.execute('select count(*) from accounts').fetchone()[0]}")

    inserted = updated = skipped = 0
    # Map source account dataset_name -> keep for users table remapping by name
    for row in src.execute("select * from accounts").fetchall():
        data = {c: row[c] for c in shared_acc}
        email = (data.get("email") or "").strip().lower()
        if not email:
            skipped += 1
            continue
        data["email"] = email

        existing = dst.execute(
            "select id, dataset_id, username, google_sub, palmpay_account_id from accounts where lower(email)=?",
            (email,),
        ).fetchone()

        # Avoid unique collisions on dataset_id / username / google_sub when inserting
        if existing is None:
            ds = data.get("dataset_id")
            if ds and dst.execute("select id from accounts where dataset_id=?", (ds,)).fetchone():
                data["dataset_id"] = f"{str(ds)[:4]}{inserted + 1:04d}"[:8]
            uname = data.get("username")
            if uname and dst.execute("select id from accounts where username=?", (uname,)).fetchone():
                data["username"] = f"{uname}_{inserted + 1}"[:64]
            gsub = data.get("google_sub")
            if gsub and dst.execute("select id from accounts where google_sub=?", (gsub,)).fetchone():
                data["google_sub"] = None
            # Don't steal existing palmpay_account_id links belonging to others
            ppid = data.get("palmpay_account_id")
            if ppid and dst.execute(
                "select id from accounts where palmpay_account_id=?", (ppid,)
            ).fetchone():
                data["palmpay_account_id"] = None

            keys = ",".join(shared_acc)
            qs = ",".join("?" for _ in shared_acc)
            dst.execute(
                f"insert into accounts ({keys}) values ({qs})",
                [data[c] for c in shared_acc],
            )
            inserted += 1
        else:
            # Update credentials + role + templates; keep dest link fields if set
            updates = {
                "password_hash": data.get("password_hash"),
                "full_name": data.get("full_name"),
                "role": data.get("role"),
                "email_verified": data.get("email_verified"),
                "left_template": data.get("left_template"),
                "right_template": data.get("right_template"),
            }
            # Prefer admin if either is admin
            if existing["id"] and data.get("role") == "admin":
                updates["role"] = "admin"
            if data.get("email_verified"):
                updates["email_verified"] = 1
            if data.get("google_sub") and not existing["google_sub"]:
                # only set if free
                clash = dst.execute(
                    "select id from accounts where google_sub=? and id!=?",
                    (data["google_sub"], existing["id"]),
                ).fetchone()
                if not clash:
                    updates["google_sub"] = data["google_sub"]

            sets = ", ".join(f"{k}=?" for k in updates)
            dst.execute(
                f"update accounts set {sets} where id=?",
                [*updates.values(), existing["id"]],
            )
            updated += 1

    dst.commit()
    print(f"Accounts inserted={inserted} updated={updated} skipped={skipped}")
    print(f"Dest accounts after: {dst.execute('select count(*) from accounts').fetchone()[0]}")

    # Copy users + enrollment_samples for dataset names that exist on dest accounts
    if "users" in [r[0] for r in src.execute("select name from sqlite_master where type='table'")]:
        dest_names = {
            r[0]
            for r in dst.execute("select dataset_name from accounts").fetchall()
            if r[0]
        }
        src_user_cols = cols(src, "users")
        dst_user_cols = cols(dst, "users")
        shared_user = [c for c in src_user_cols if c in dst_user_cols and c != "id"]

        # Map src user_id -> dest user_id
        id_map: dict[int, int] = {}
        users_ins = users_upd = 0
        for u in src.execute("select * from users").fetchall():
            name = u["name"]
            hand = u["hand"]
            if name not in dest_names:
                continue
            existing_u = dst.execute(
                "select id from users where name=? and hand=?", (name, hand)
            ).fetchone()
            payload = {c: u[c] for c in shared_user}
            if existing_u:
                sets = ", ".join(f"{k}=?" for k in shared_user)
                dst.execute(
                    f"update users set {sets} where id=?",
                    [*[payload[c] for c in shared_user], existing_u["id"]],
                )
                id_map[u["id"]] = existing_u["id"]
                users_upd += 1
            else:
                keys = ",".join(shared_user)
                qs = ",".join("?" for _ in shared_user)
                cur = dst.execute(
                    f"insert into users ({keys}) values ({qs})",
                    [payload[c] for c in shared_user],
                )
                id_map[u["id"]] = cur.lastrowid
                users_ins += 1
        dst.commit()
        print(f"Users inserted={users_ins} updated={users_upd} mapped={len(id_map)}")

        if "enrollment_samples" in [
            r[0] for r in src.execute("select name from sqlite_master where type='table'")
        ] and id_map:
            src_es = cols(src, "enrollment_samples")
            dst_es = cols(dst, "enrollment_samples")
            shared_es = [c for c in src_es if c in dst_es and c != "id"]
            # clear samples for remapped users then re-copy
            for dest_uid in set(id_map.values()):
                dst.execute("delete from enrollment_samples where user_id=?", (dest_uid,))
            es_ins = 0
            for s in src.execute("select * from enrollment_samples").fetchall():
                src_uid = s["user_id"]
                if src_uid not in id_map:
                    continue
                payload = {c: s[c] for c in shared_es}
                payload["user_id"] = id_map[src_uid]
                keys = ",".join(shared_es)
                qs = ",".join("?" for _ in shared_es)
                dst.execute(
                    f"insert into enrollment_samples ({keys}) values ({qs})",
                    [payload[c] for c in shared_es],
                )
                es_ins += 1
            dst.commit()
            print(f"Enrollment samples inserted={es_ins}")

    print("--- Dest accounts ---")
    for r in dst.execute(
        "select id, email, role, email_verified from accounts order by id"
    ):
        print(dict(r))

    src.close()
    dst.close()
    print("DONE")


if __name__ == "__main__":
    main()
