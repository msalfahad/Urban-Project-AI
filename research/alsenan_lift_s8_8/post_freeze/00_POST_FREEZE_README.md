# S8.8 post-freeze comparison

Run after the freeze (`18_S8_8_FREEZE_MANIFEST.json`, sha256 `fd1655dc3f60dde6...`, verified
before and after). It compares by equal physical scope and changes nothing.

- **V3b has 0 lift lines.** The pit walls, their bars and the P8-N19 tie beam were missing from
  the old population. S8.8 populates them and releases 0 m3 / 0 kg: the pit depth is the lift manufacturer's, and no
  tie-beam section is stated.
- **The FF footing volume agrees everywhere.** V3b's footing line has 11.385 m3 for FF, the freelancer
  crosswalk has 11.385 m3, and S8.8 computes 11.385 m3. S8.8 does not release it:
  the footing family owns it.
- **PRE-S8 had no lift figure.** It recorded the lift as NOT_MEASURED. Its footing state quotes the whole V3b footing
  line against one footing, a scope difference. The ownership gap for the wall bars is now closed by assignment
  (S8.8, blocked).
- **The freelancer reading of the S-BW boxes is the one S8.8 applies.** The boxes are the lift-pit and pool walls,
  and the 3.24 m2 pit opening matches.

Classes: AUTHORITY 2, METHOD 1, MISSED_OBJECT 1, NOT_COMPARABLE 1, NO_DIFFERENCE 8, SCOPE 3.
