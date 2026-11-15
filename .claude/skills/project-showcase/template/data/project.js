// Every word, number and position on the site comes from this file.
// Fill it from the unit schedule, finishes schedule and model, never by hand-guessing.
// A scene with frames: null draws a code placeholder. Point it at a rendered sequence to swap in the real thing.
window.PROJECT = {
  name: "Placeholder Residences",
  address: "Site address TBC",
  tagline: "Twelve levels. Placeholder copy until the developer signs off the words.",
  enquireUrl: "#enquire",
  disclaimer: "Artist's impression. Final design, finishes and views may vary.",
  finishesRevision: "Finishes schedule revision TBC",

  levels: 12,

  scenes: {
    // frames: { desktop: { path: "frames/hero/desktop/{i}.webp", count: 180, pad: 4 }, mobile: { path: "frames/hero/mobile/{i}.webp", count: 120, pad: 4 } }
    hero: { frames: null, focusLevel: 10 },
    picker: { image: null } // one still of the tower, same camera the hotspot x/y were exported from
  },

  // x and y are % of the picker image. Export them from the model's room centroids.
  units: [
    { id: "12.01", type: "A", level: 12, beds: 3, baths: 2, internal: 0, external: 0, aspect: "TBC", status: "Available", x: 42, y: 13.3 },
    { id: "10.02", type: "B", level: 10, beds: 2, baths: 2, internal: 0, external: 0, aspect: "TBC", status: "Available", x: 58, y: 26.7 },
    { id: "06.01", type: "A", level: 6, beds: 3, baths: 2, internal: 0, external: 0, aspect: "TBC", status: "Reserved", x: 42, y: 53.3 },
    { id: "03.02", type: "B", level: 3, beds: 2, baths: 2, internal: 0, external: 0, aspect: "TBC", status: "Available", x: 58, y: 73.3 }
  ],

  // One cutaway sequence per apartment type. Room rects are plan metres [x, y, w, h] from the model.
  // "at" is the slice of the scroll [start, end] where that room's caption shows.
  types: {
    A: {
      name: "Type A",
      frames: null,
      plan: { w: 14, h: 9 },
      rooms: [
        { name: "Living and dining", caption: "Placeholder caption. Pull the real one from the finishes schedule.", rect: [0, 0, 8, 5.5], at: [0.15, 0.4] },
        { name: "Kitchen", caption: "Placeholder caption.", rect: [8, 0, 6, 4], at: [0.4, 0.6] },
        { name: "Main bedroom", caption: "Placeholder caption.", rect: [0, 5.5, 5.5, 3.5], at: [0.6, 0.8] },
        { name: "Main bathroom", caption: "Placeholder caption.", rect: [5.5, 5.5, 3, 3.5], at: [0.8, 1] },
        { name: "Bedroom 2", rect: [8.5, 4, 5.5, 5] }
      ]
    },
    B: {
      name: "Type B",
      frames: null,
      plan: { w: 11, h: 8 },
      rooms: [
        { name: "Living and kitchen", caption: "Placeholder caption.", rect: [0, 0, 7, 5], at: [0.15, 0.5] },
        { name: "Main bedroom", caption: "Placeholder caption.", rect: [7, 0, 4, 4.5], at: [0.5, 0.75] },
        { name: "Bathroom", caption: "Placeholder caption.", rect: [7, 4.5, 4, 3.5], at: [0.75, 1] },
        { name: "Bedroom 2", rect: [0, 5, 7, 3] }
      ]
    }
  },

  finishes: [
    { area: "Kitchen", item: "Benchtop", supplier: "Supplier TBC", code: "Code TBC" },
    { area: "Kitchen", item: "Appliances", supplier: "Supplier TBC", code: "Code TBC" },
    { area: "Bathroom", item: "Wall tile", supplier: "Supplier TBC", code: "Code TBC" },
    { area: "Bathroom", item: "Tapware", supplier: "Supplier TBC", code: "Code TBC" },
    { area: "Living", item: "Flooring", supplier: "Supplier TBC", code: "Code TBC" },
    { area: "Bedrooms", item: "Carpet", supplier: "Supplier TBC", code: "Code TBC" }
  ],

  // Builder's edge: the same room photographed at frame stage and at handover, same camera spot.
  progress: [
    { room: "Living", before: { label: "Frame stage", src: null }, after: { label: "Handover", src: null } },
    { room: "Kitchen", before: { label: "Frame stage", src: null }, after: { label: "Handover", src: null } },
    { room: "Main bedroom", before: { label: "Frame stage", src: null }, after: { label: "Handover", src: null } }
  ]
};
