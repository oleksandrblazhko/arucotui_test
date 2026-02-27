void keyPressed() {
  if (key == ' ') {
    homographyMatrixCalculated = false;
  }
  if (key == 'r') {
    resetDataObjects();
  }
  if (key == 'g') {
    gestureDebug = !gestureDebug;
  }
  if (key == 't') {
    tagDebug= !tagDebug;
  }
  if (key == 'd') {
    dataObjectDebug = !dataObjectDebug;
  }
  if (key == 's') {
    serialDebug= !serialDebug;
  }
  if (key >= '1' && key <= '3') {
    gestureMode = key - '0';
  }
}
