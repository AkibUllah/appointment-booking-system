"""Seed demo data: `python -m app.seed`. Safe to run repeatedly (skips when doctors exist)."""

from __future__ import annotations

import logging
from datetime import time

from sqlalchemy import select

from app.core.logging import configure_logging
from app.db.models import AvailabilityTemplate, Base, Chamber, Doctor, Specialty
from app.db.session import SessionLocal, engine

log = logging.getLogger("seed")

SPECIALTIES = [
    ("Cardiology", "হৃদরোগ"),
    ("Dermatology", "চর্মরোগ"),
    ("Paediatrics", "শিশুরোগ"),
    ("Gynaecology", "স্ত্রীরোগ"),
    ("Orthopaedics", "অর্থোপেডিক্স"),
    ("ENT", "নাক-কান-গলা"),
    ("General Medicine", "মেডিসিন"),
]

CHAMBERS = [
    (
        "Sunflower Diagnostic, Dhanmondi",
        "Dhanmondi",
        "House 12, Road 7, Dhanmondi R/A, Dhaka 1205",
        "+8801700000101",
    ),
    (
        "Riverbank Medical Centre, Shyamoli",
        "Shyamoli",
        "House 40, Mirpur Road, Shyamoli, Dhaka 1207",
        "+8801700000102",
    ),
    (
        "Lakeside Chamber, Gulshan",
        "Gulshan",
        "House 9, Road 103, Gulshan 2, Dhaka 1212",
        "+8801700000103",
    ),
    (
        "Northpoint Diagnostic, Uttara",
        "Uttara",
        "House 21, Road 14, Sector 7, Uttara, Dhaka 1230",
        "+8801700000104",
    ),
    (
        "Citycare Chamber, Motijheel",
        "Motijheel",
        "18 Dilkusha C/A, Motijheel, Dhaka 1000",
        "+8801700000105",
    ),
    (
        "Mirpur Specialised Chamber",
        "Mirpur",
        "Plot 7, Section 10, Mirpur, Dhaka 1216",
        "+8801711000000",
    ),
]

# (name, name_bn, degrees, specialty, chamber index, slot_minutes, fee, exp, weekday windows)
# Weekday: 0=Mon ... 6=Sun. Friday (4) is the weekly holiday for most chambers.
DOCTORS = [
    (
        "Dr. Farhana Rahman",
        "ডা. ফারহানা রহমান",
        "MBBS, MD (Cardiology)",
        "Cardiology",
        0,
        15,
        1200,
        14,
        [
            (5, "17:00", "21:00"),
            (6, "17:00", "21:00"),
            (1, "17:00", "21:00"),
            (3, "17:00", "21:00"),
        ],
    ),
    (
        "Dr. Tanvir Ahmed",
        "ডা. তানভীর আহমেদ",
        "MBBS, FCPS (Medicine)",
        "General Medicine",
        1,
        10,
        800,
        9,
        [(5, "18:00", "22:00"), (0, "18:00", "22:00"), (2, "18:00", "22:00")],
    ),
    (
        "Dr. Nusrat Jahan",
        "ডা. নুসরাত জাহান",
        "MBBS, DDV, MCPS (Dermatology)",
        "Dermatology",
        2,
        20,
        1500,
        11,
        [(6, "16:00", "20:00"), (1, "16:00", "20:00"), (3, "16:00", "20:00")],
    ),
    (
        "Dr. Mahbub Alam",
        "ডা. মাহবুব আলম",
        "MBBS, DCH, FCPS (Paediatrics)",
        "Paediatrics",
        3,
        15,
        1000,
        18,
        [
            (5, "09:00", "13:00"),
            (0, "17:00", "21:00"),
            (2, "17:00", "21:00"),
            (6, "09:00", "13:00"),
        ],
    ),
    (
        "Dr. Shirin Akter",
        "ডা. শিরিন আক্তার",
        "MBBS, FCPS (Gynae & Obs)",
        "Gynaecology",
        0,
        20,
        1200,
        16,
        [(0, "15:00", "19:00"), (2, "15:00", "19:00"), (5, "10:00", "14:00")],
    ),
    (
        "Dr. Kamrul Hasan",
        "ডা. কামরুল হাসান",
        "MBBS, MS (Ortho)",
        "Orthopaedics",
        4,
        15,
        1000,
        12,
        [(6, "18:00", "21:00"), (1, "18:00", "21:00"), (3, "18:00", "21:00")],
    ),
    (
        "Dr. Rezaul Karim",
        "ডা. রেজাউল করিম",
        "MBBS, DLO (ENT)",
        "ENT",
        5,
        10,
        700,
        8,
        [
            (5, "17:00", "21:00"),
            (0, "17:00", "21:00"),
            (2, "17:00", "21:00"),
            (6, "17:00", "21:00"),
        ],
    ),
    (
        "Dr. Sadia Islam",
        "ডা. সাদিয়া ইসলাম",
        "MBBS, MD (Cardiology)",
        "Cardiology",
        2,
        15,
        1500,
        10,
        [(0, "17:00", "20:00"), (3, "17:00", "20:00")],
    ),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(Doctor.id).limit(1)) is not None:
            log.info("database already seeded; nothing to do")
            return
        specialties = {name: Specialty(name=name, name_bn=bn) for name, bn in SPECIALTIES}
        chambers = [Chamber(name=n, area=a, address=ad, phone=p) for n, a, ad, p in CHAMBERS]
        db.add_all(specialties.values())
        db.add_all(chambers)
        db.flush()
        for name, name_bn, degrees, spec, ch_idx, slot, fee, exp, windows in DOCTORS:
            doctor = Doctor(
                name=name,
                name_bn=name_bn,
                degrees=degrees,
                specialty_id=specialties[spec].id,
                chamber_id=chambers[ch_idx].id,
                slot_minutes=slot,
                fee_bdt=fee,
                experience_years=exp,
            )
            for weekday, start, end in windows:
                doctor.templates.append(
                    AvailabilityTemplate(
                        weekday=weekday,
                        start_time=time.fromisoformat(start),
                        end_time=time.fromisoformat(end),
                    )
                )
            db.add(doctor)
        db.commit()
        log.info(
            "seeded %d specialties, %d chambers, %d doctors",
            len(SPECIALTIES),
            len(CHAMBERS),
            len(DOCTORS),
        )
    finally:
        db.close()


if __name__ == "__main__":
    configure_logging()
    seed()
