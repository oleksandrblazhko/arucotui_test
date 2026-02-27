boolean resetData = false;
boolean gestureDebug = false;
boolean dataObjectDebug = false;
boolean tagDebug = false;
boolean serialDebug = false;

PVector[] srcPoints = new PVector[4];
PVector[] dstPoints = new PVector[4];
PVector[] planePoints = new PVector[4];

boolean homographyMatrixCalculated = false;
SimpleMatrix homography;

ArrayList idTOs;
ArrayList offsetTOs;
PImage calibImg; //the calibration image
int[] cornersID = {1, 3, 2, 0}; //the corner markers of the calibration image. only the first three are used.
float tag2screenRatio = 297. / paperWidthOnScreen; //1
PVector cCen = new PVector (842./2., 595./2.);
float mW = (markerWidth/25.4*72.)*tag2screenRatio;
float calibgridWidth = 100+markerWidth; //unit:mm
float calibgridHeight = 100+markerWidth; //unit:mm
float mDC1 = (calibgridWidth/2)*(72/25.4)*tag2screenRatio;
float mDC2 = (calibgridHeight/2)*(72/25.4)*tag2screenRatio;
float[] markerX = {(cCen.x-mDC1+mW/2), (cCen.x-mDC1+mW/2), (cCen.x+mDC2-mW/2), (cCen.x+mDC2-mW/2)};
float[] markerY = {(cCen.y-mDC1+mW/2), (cCen.y+mDC1+mW/2), (cCen.y-mDC2-mW/2), (cCen.y+mDC2-mW/2)};
float markerGridWidth = markerX[2]-markerX[0];
PVector markerOffset = new PVector(markerX[0], markerY[0]);
PVector windowOffset = new PVector(0, 0);
PVector imageOffset = new PVector(0, 0);
float global_rx=0;
float global_ry=0;
float global_rz=0;
float alpha = 0;

boolean drawing = false; //when token does not hit the dataobject, set drawMode as true

void initTagManager() {
  idTOs = new ArrayList();
  offsetTOs = new ArrayList();
  for (int i = 0; i < TO_IDs.length; i++) {
    ArrayList ids = new ArrayList();
    ArrayList offsets = new ArrayList();
    for (int j = 0; j < TO_IDs[i].length; j++) {
      ids.add(TO_IDs[i][j]);
      offsets.add(TO_Offsets[i][j]);
    }
    idTOs.add(ids);
    offsetTOs.add(offsets);
  }
  tm = new TagManager(600, idTOs, offsetTOs);
}

void loadCalibrationImg(String s) {
  calibImg = loadImage(s); //select the calibration image
  imageOffset.set((width - calibImg.width)/2, (height - calibImg.height)/2); //center the calibration image
}


void calculateHomographyMatrix() {
  srcPoints[0] = new PVector(tm.tags[cornersID[0]].tx, tm.tags[cornersID[0]].ty, tm.tags[cornersID[0]].tz);
  srcPoints[1] = new PVector(tm.tags[cornersID[1]].tx, tm.tags[cornersID[1]].ty, tm.tags[cornersID[1]].tz);
  srcPoints[2] = new PVector(tm.tags[cornersID[2]].tx, tm.tags[cornersID[2]].ty, tm.tags[cornersID[2]].tz);

  dstPoints[0] = new PVector(0, 0);
  dstPoints[1] = new PVector(1, 0);
  dstPoints[2] = new PVector(1, 1);
  
  homography = calculateHomography(srcPoints, dstPoints);
}

void registerPlanePoints() {
  planePoints[0] = new PVector(srcPoints[0].x, srcPoints[0].y, srcPoints[0].z);
  planePoints[1] = new PVector(srcPoints[1].x, srcPoints[1].y, srcPoints[1].z);
  planePoints[2] = new PVector(srcPoints[2].x, srcPoints[2].y, srcPoints[2].z);
}

void registerPlaneOrientation(){
  global_rx= (tm.tags[cornersID[0]].rx + tm.tags[cornersID[1]].rx + tm.tags[cornersID[2]].rx)/3;
  global_ry= (tm.tags[cornersID[0]].ry + tm.tags[cornersID[1]].ry + tm.tags[cornersID[2]].ry)/3;
  global_rz= (tm.tags[cornersID[0]].rz + tm.tags[cornersID[1]].rz + tm.tags[cornersID[2]].rz)/3;
  println(global_rx,global_ry,global_rz);
}

boolean cornersDetected() {
  if (tm.tags[cornersID[0]].active &&
    tm.tags[cornersID[1]].active &&
    tm.tags[cornersID[2]].active) {
    return true;
  } else {
    return false;
  }
}

boolean isCorner(int id) {
  if (id == cornersID[0] || id == cornersID[1] || id == cornersID[2]){
    return true;
  } else {
    return false;
  }
}

SimpleMatrix calculateHomography(PVector[] srcPoints, PVector[] dstPoints) {
  SimpleMatrix srcMatrix = new SimpleMatrix(3, 3);
  SimpleMatrix dstMatrix = new SimpleMatrix(3, 3);

  for (int i = 0; i < 3; i++) {
    srcMatrix.set(0, i, srcPoints[i].x);
    srcMatrix.set(1, i, srcPoints[i].y);
    srcMatrix.set(2, i, srcPoints[i].z);

    dstMatrix.set(0, i, dstPoints[i].x);
    dstMatrix.set(1, i, dstPoints[i].y);
    dstMatrix.set(2, i, 1.0);
  }

  return dstMatrix.mult(srcMatrix.pseudoInverse());
}

PVector transformPoint(PVector point, SimpleMatrix homography) {
  float x = point.x;
  float y = point.y;
  float z = point.z;

  SimpleMatrix result = homography.mult(new SimpleMatrix(new double[][] {{x}, {y}, {z}}));

  float w = (float) result.get(2, 0);
  float transformedX = (float) (result.get(0, 0) / w);
  float transformedY = (float) (result.get(1, 0) / w);

  return new PVector(transformedX, transformedY);
}

PVector img2screen(PVector p) {
  PVector wo = windowOffset;
  PVector io = imageOffset;
  PVector mo = markerOffset;
  float mgw = markerGridWidth;
  return new PVector (p.x*mgw + wo.x + io.x + mo.x, p.y*mgw + wo.y + io.y + mo.y);
}

float distancePointToPlane(PVector point, PVector[] planePoints) {
  PVector normal = cross(subtract(planePoints[1], planePoints[0]), subtract(planePoints[2], planePoints[0])); // Calculate the normal vector to the plane
  float d = -dot(normal, planePoints[0]); // Calculate the d coefficient of the plane equation

  // Use the plane equation to find the distance
  float numerator = abs(dot(normal, point) + d);
  float denominator = sqrt(pow(normal.x, 2) + pow(normal.y, 2) + pow(normal.z, 2));

  return numerator / denominator;
}

PVector cross(PVector v1, PVector v2) {
  return new PVector(
    v1.y * v2.z - v1.z * v2.y,
    v1.z * v2.x - v1.x * v2.z,
    v1.x * v2.y - v1.y * v2.x
    );
}

float dot(PVector v1, PVector v2) {
  return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
}

PVector subtract(PVector v1, PVector v2) {
  return new PVector(v1.x - v2.x, v1.y - v2.y, v1.z - v2.z);
}

float getDistanceBetween(PVector p0, PVector p1) {
  return dist(p0.x, p0.y, p1.x, p1.y);
}

float getAngleBetween(PVector p0, PVector p1) {
  return atan2(p1.y-p0.y, p1.x-p0.x);
}

PVector getCentroidBetween(PVector p0, PVector p1) {
  return PVector.add(p0, p1).div(2);
}
