# Sample house

The buildingSMART IFC4 sample house (public), used to test the pipeline end to end and to benchmark render speed.

- `shots.json`: the full showcase (hero orbit, cutaway, living room walk, picker, plan), EEVEE drafts.
- `bench.json`: a fixed Cycles benchmark (one 1920x1080 still, a 24-frame 960x540 room move) for comparing machines. Same file on every machine, so timings compare.
- `finishes.csv`: colours for the sample's IFC materials (no textures, so it runs anywhere).

Get the model: download `Building-Architecture.ifc` from buildingSMART's Sample-Test-Files repo (IFC 4.0.2.1 / Simple-Scene), then `python ../../scripts/ifc_to_obj.py Building-Architecture.ifc work/` and copy `../../template` to `site/`. The Kaggle notebook in `../../kaggle/` does all of this for you.
