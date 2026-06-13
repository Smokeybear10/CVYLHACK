// Sonder CAD viewer: load the scene and open the camera right on the EV charger, highlighted.
// No dragging, no editing, no buttons. The charger is auto-placed by run.py on an open curb spot.
let viewer;

Autodesk.Viewing.Initializer({
  env: "AutodeskProduction2", api: "streamingV2",
  getAccessToken: cb => fetch("/api/token").then(r => r.json())
    .then(t => cb(t.access_token, t.expires_in)),
}, () => {
  viewer = new Autodesk.Viewing.GuiViewer3D(document.getElementById("v"));
  viewer.start();
  Autodesk.Viewing.Document.load("urn:" + URN, doc => {
    viewer.loadDocumentNode(doc, doc.getRoot().getDefaultGeometry(), { useConsolidation: false })
      .then(frameCharger);
  }, err => console.error("load failed", err));
});

// Find every part of the charger (names start with "ev_charger"), union their boxes, point the
// camera at it, and highlight it so it is immediately obvious where the charger is on the map.
function frameCharger() {
  viewer.navigation.setWorldUpVector(new THREE.Vector3(0, 0, 1), true);   // survey data is Z-up
  const tree = viewer.model.getInstanceTree();
  const ids = [];
  let minx = Infinity, miny = Infinity, minz = Infinity, maxx = -Infinity, maxy = -Infinity, maxz = -Infinity;
  tree.enumNodeChildren(tree.getRootId(), id => {
    if (tree.getChildCount(id) !== 0) return;
    const name = tree.getNodeName(id) || "";
    if (name.indexOf("ev_charger") === 0) {
      ids.push(id);
      const b = new Float32Array(6); tree.getNodeBox(id, b);
      minx = Math.min(minx, b[0]); miny = Math.min(miny, b[1]); minz = Math.min(minz, b[2]);
      maxx = Math.max(maxx, b[3]); maxy = Math.max(maxy, b[4]); maxz = Math.max(maxz, b[5]);
    }
  }, true);

  if (ids.length) {
    const cx = (minx + maxx) / 2, cy = (miny + maxy) / 2, cz = (minz + maxz) / 2;
    const eye = new THREE.Vector3(cx - 9, cy - 9, cz + 5);   // a few meters away, slightly above
    viewer.navigation.setView(eye, new THREE.Vector3(cx, cy, cz));
    viewer.navigation.setCameraUpVector(new THREE.Vector3(0, 0, 1));
    viewer.select(ids);                                       // highlight the charger
    console.log("charger framed:", ids.length, "parts at", cx.toFixed(1), cy.toFixed(1));
  } else {
    // no charger in this scene: fall back to a street-level view of the block
    const bb = viewer.model.getBoundingBox(), c = bb.center();
    viewer.navigation.setView(new THREE.Vector3(c.x, bb.min.y - 15, bb.min.z + 2),
                              new THREE.Vector3(c.x, c.y, bb.min.z + 2));
    viewer.navigation.setCameraUpVector(new THREE.Vector3(0, 0, 1));
  }
}
