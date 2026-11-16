// Every word, number and position on the site comes from this file (plus frames/manifest.js, which
// the render script writes). Fill it from the unit and finishes schedules, never by guessing.
//
// The page is a list of sections. Reorder them, delete them, or set off: true. Kinds:
//   scrub    a scroll-driven rendered sequence (hero, orbit, flythrough, corridor, plan reveal, room)
//   cutaway  one sequence per type (apartment type, house design, tenancy), room captions, room rail
//   picker   hotspots on a still; units link to a cutaway type
//   stats    key figures (GFA, lots, car parks, completion)
//   specs    finishes and inclusions
//   compare  before/after slider: frame stage vs handover, existing vs proposed, month vs month
// A section whose data is missing is skipped and logged; the rest of the page still builds.
// "frames" is the shot name from shots.json. Until it's rendered the scene draws a stamped placeholder.
window.PROJECT = {
  name: "Placeholder Residences",
  address: "Site address TBC",
  description: "Placeholder description for search results and link previews.",
  disclaimer: "Artist's impression. Final design, finishes and views may vary.",
  sourceRevision: "Rendered from drawing revision TBC, finishes schedule revision TBC.",
  enquire: { label: "Enquire", href: "mailto:sales@example.com" },

  sections: [
    {
      id: "hero", kind: "scrub", hero: true, frames: "hero", length: 3, still: 0,
      alt: "Exterior of the building, camera moving in",
      placeholder: { kind: "tower", levels: 12, focusLevel: 10 },
      copy: { eyebrow: "Site address TBC", title: "Placeholder Residences", text: "Placeholder line until the developer signs off the words." }
    },
    {
      id: "residences", kind: "picker", nav: "Residences", frames: "picker", link: "inside",
      copy: { eyebrow: "Residences", title: "Pick a home on the building." },
      labels: { unit: "Residence", cta: "See inside" },
      placeholder: { levels: 12 },
      fields: [
        { key: "typeName", label: "Type" }, { key: "level", label: "Level" },
        { key: "beds", label: "Bedrooms" }, { key: "baths", label: "Bathrooms" },
        { key: "internal", label: "Internal", unit: "m²" }, { key: "external", label: "External", unit: "m²" },
        { key: "aspect", label: "Aspect" }
      ],
      // anchor = space or unit name in the model; the render script writes its exact x/y into frames/manifest.js.
      // x/y here (in % of the still) are only a fallback for the placeholder.
      units: [
        { id: "12.01", type: "A", typeName: "Type A", level: 12, beds: 3, baths: 2, internal: null, external: null, aspect: null, status: "Available", x: 42, y: 13.3 },
        { id: "10.02", type: "B", typeName: "Type B", level: 10, beds: 2, baths: 2, internal: null, external: null, aspect: null, status: "Available", x: 58, y: 26.7 },
        { id: "06.01", type: "A", typeName: "Type A", level: 6, beds: 3, baths: 2, internal: null, external: null, aspect: null, status: "Reserved", x: 42, y: 53.3 },
        { id: "03.02", type: "B", typeName: "Type B", level: 3, beds: 2, baths: 2, internal: null, external: null, aspect: null, status: "Available", x: 58, y: 73.3 }
      ]
    },
    {
      id: "inside", kind: "cutaway", nav: "Inside", length: 5, typeLabel: "Apartment type",
      types: {
        A: {
          name: "Type A", frames: "inside_a", plan: { w: 14, h: 9 },
          rooms: [
            { name: "Living and dining", caption: "Placeholder caption from the finishes schedule.", rect: [0, 0, 8, 5.5], at: [0.15, 0.4] },
            { name: "Kitchen", caption: "Placeholder caption.", rect: [8, 0, 6, 4], at: [0.4, 0.6] },
            { name: "Main bedroom", caption: "Placeholder caption.", rect: [0, 5.5, 5.5, 3.5], at: [0.6, 0.8] },
            { name: "Main bathroom", caption: "Placeholder caption.", rect: [5.5, 5.5, 3, 3.5], at: [0.8, 1] },
            { name: "Bedroom 2", rect: [8.5, 4, 5.5, 5] }
          ]
        },
        B: {
          name: "Type B", frames: "inside_b", plan: { w: 11, h: 8 },
          rooms: [
            { name: "Living and kitchen", caption: "Placeholder caption.", rect: [0, 0, 7, 5], at: [0.15, 0.5] },
            { name: "Main bedroom", caption: "Placeholder caption.", rect: [7, 0, 4, 4.5], at: [0.5, 0.75] },
            { name: "Bathroom", caption: "Placeholder caption.", rect: [7, 4.5, 4, 3.5], at: [0.75, 1] },
            { name: "Bedroom 2", rect: [0, 5, 7, 3] }
          ]
        }
      }
    },
    {
      id: "figures", kind: "stats",
      items: [{ value: null, source: "units", label: "Residences" }, { value: null, source: "levels", label: "Levels" }, { value: null, label: "Completion" }]
    },
    {
      id: "finishes", kind: "specs", nav: "Finishes",
      copy: { eyebrow: "Finishes", title: "Specified, not imagined.", text: "Finishes schedule revision TBC." },
      items: [
        { area: "Kitchen", item: "Benchtop", supplier: null, code: null },
        { area: "Kitchen", item: "Appliances", supplier: null, code: null },
        { area: "Bathroom", item: "Wall tile", supplier: null, code: null },
        { area: "Living", item: "Flooring", supplier: null, code: null }
      ]
    },
    {
      id: "build", kind: "compare", nav: "The build", tabsLabel: "Room",
      copy: { eyebrow: "The build", title: "Same room. Frame stage to handover." },
      // Two photos from the same tripod spot. Placeholders show until src is set.
      pairs: [
        { label: "Living", before: { label: "Frame stage", src: null, alt: "" }, after: { label: "Handover", src: null, alt: "" } },
        { label: "Kitchen", before: { label: "Frame stage", src: null, alt: "" }, after: { label: "Handover", src: null, alt: "" } }
      ]
    }
  ]
};
