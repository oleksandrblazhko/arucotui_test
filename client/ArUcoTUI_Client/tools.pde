boolean resetData = false;
boolean gestureDebug = false;
boolean dataObjectDebug = false;
boolean tagDebug = false;
boolean serialDebug = false;

PVector[] srcPointsT = new PVector[4];
PVector[] dstPointsT = new PVector[4];
PVector[] srcPointsR = new PVector[4];
PVector[] dstPointsR = new PVector[4];
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

void loadCalibrationFile(String filename) {
  String[] lines;
  try {
    lines = loadStrings(filename);
    if (lines == null) {
      throw new RuntimeException("File not found: srcPoints.txt");
    }
    // Initialize and parse srcPoints
    PVector[] cornerPointsT = new PVector[lines.length];
    PVector[] cornerPointsR = new PVector[lines.length];
    for (int i = 0; i < lines.length; i++) {
      String[] coords = split(lines[i], ",");
      float tx = float(trim(coords[0]));
      float ty = float(trim(coords[1]));
      float tz = float(trim(coords[2]));
      float rx = float(trim(coords[3]));
      float ry = float(trim(coords[4]));
      float rz = float(trim(coords[5]));
      cornerPointsT[i] = new PVector(tx, ty, tz);
      cornerPointsR[i] = new PVector(rx, ry, rz);
      println(tx, ty, tz, rx, ry, rz);
    }
    calculateHomographyMatrix(cornerPointsT); //calculate the homography matrix
    registerPlanePoints(); //register the plane points for plane calculation.
    registerPlaneOrientation(cornerPointsR); //register the plane orientation for plane calculation.
    homographyMatrixCalculated = true; //set the homography matrix flag to "calculated"
  }
  catch (Exception e) {
    println("Error loading file: " + e.getMessage());
  }
}

void saveCalibrationFile(String filename) {
  srcPointsT[0] = new PVector(tm.tags[cornersID[0]].tx, tm.tags[cornersID[0]].ty, tm.tags[cornersID[0]].tz);
  srcPointsT[1] = new PVector(tm.tags[cornersID[1]].tx, tm.tags[cornersID[1]].ty, tm.tags[cornersID[1]].tz);
  srcPointsT[2] = new PVector(tm.tags[cornersID[2]].tx, tm.tags[cornersID[2]].ty, tm.tags[cornersID[2]].tz);
  srcPointsR[0] = new PVector(tm.tags[cornersID[0]].rx, tm.tags[cornersID[0]].ry, tm.tags[cornersID[0]].rz);
  srcPointsR[1] = new PVector(tm.tags[cornersID[1]].rx, tm.tags[cornersID[1]].ry, tm.tags[cornersID[1]].rz);
  srcPointsR[2] = new PVector(tm.tags[cornersID[2]].rx, tm.tags[cornersID[2]].ry, tm.tags[cornersID[2]].rz);
  String[] lines = new String[3];
  for (int i = 0; i < 3; i++) {
    lines[i] = nf((float)srcPointsT[i].x, 0, 3) + ", " + nf((float)srcPointsT[i].y, 0, 3) + ", " + nf((float)srcPointsT[i].z, 0, 3)+ ", " +
               nf((float)srcPointsR[i].x, 0, 3) + ", " + nf((float)srcPointsR[i].y, 0, 3) + ", " + nf((float)srcPointsR[i].z, 0, 3);
    println(lines[i]);
  }
  saveStrings("corners.txt", lines);
}
void calculateHomographyMatrix(PVector[] cornerPointsT) {
  srcPointsT[0] = new PVector(cornerPointsT[0].x, cornerPointsT[0].y, cornerPointsT[0].z);
  srcPointsT[1] = new PVector(cornerPointsT[1].x, cornerPointsT[1].y, cornerPointsT[1].z);
  srcPointsT[2] = new PVector(cornerPointsT[2].x, cornerPointsT[2].y, cornerPointsT[2].z);

  dstPointsT[0] = new PVector(0, 0);
  dstPointsT[1] = new PVector(1, 0);
  dstPointsT[2] = new PVector(1, 1);

  homography = calculateHomography(srcPointsT, dstPointsT);
}


void calculateHomographyMatrix() {
  srcPointsT[0] = new PVector(tm.tags[cornersID[0]].tx, tm.tags[cornersID[0]].ty, tm.tags[cornersID[0]].tz);
  srcPointsT[1] = new PVector(tm.tags[cornersID[1]].tx, tm.tags[cornersID[1]].ty, tm.tags[cornersID[1]].tz);
  srcPointsT[2] = new PVector(tm.tags[cornersID[2]].tx, tm.tags[cornersID[2]].ty, tm.tags[cornersID[2]].tz);

  dstPointsT[0] = new PVector(0, 0);
  dstPointsT[1] = new PVector(1, 0);
  dstPointsT[2] = new PVector(1, 1);
  
  homography = calculateHomography(srcPointsT, dstPointsT);
}

void registerPlanePoints() {
  planePoints[0] = new PVector(srcPointsT[0].x, srcPointsT[0].y, srcPointsT[0].z);
  planePoints[1] = new PVector(srcPointsT[1].x, srcPointsT[1].y, srcPointsT[1].z);
  planePoints[2] = new PVector(srcPointsT[2].x, srcPointsT[2].y, srcPointsT[2].z);
}

void registerPlaneOrientation(){
  global_rx= (tm.tags[cornersID[0]].rx + tm.tags[cornersID[1]].rx + tm.tags[cornersID[2]].rx)/3;
  global_ry= (tm.tags[cornersID[0]].ry + tm.tags[cornersID[1]].ry + tm.tags[cornersID[2]].ry)/3;
  global_rz= (tm.tags[cornersID[0]].rz + tm.tags[cornersID[1]].rz + tm.tags[cornersID[2]].rz)/3;
  println(global_rx,global_ry,global_rz);
}

void registerPlaneOrientation(PVector[] cornerPointsR){
  global_rx= (cornerPointsR[0].x + cornerPointsR[1].x + cornerPointsR[2].x)/3;
  global_ry= (cornerPointsR[0].y + cornerPointsR[1].y + cornerPointsR[2].y)/3;
  global_rz= (cornerPointsR[0].z + cornerPointsR[1].z + cornerPointsR[2].z)/3;
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
  if (id == cornersID[0] || id == cornersID[1] || id == cornersID[2]) {
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

int whichTO(int id) {
  for (int i = 0; i < TO_IDs.length; i++) {
    if (TO_IDs[i][0] == id) {
      return i;  // Return the index where the ID matches
    }
  }
  return -1;  // Return -1 if the ID is not found
}

float mmToPx (float mm){
  return mm * (72. / 25.4)*tag2screenRatio;
}

PVector getTiltAngles(PVector tilt2D, float angle2D) {
  PVector obj = new PVector(global_rx, global_ry, global_rz);
  PVector surf = new PVector(tilt2D.x, tilt2D.y, angle2D);
  // 1. Generate Rotation Matrices for both
  PMatrix3D R_s = getRotationMatrix(surf.x, surf.y, surf.z);
  PMatrix3D R_o = getRotationMatrix(obj.x, obj.y, obj.z);
  // 2. Get Relative Rotation: R_rel = (R_s^T) * R_o
  // In rotation matrices, the Transpose is the Inverse.
  R_s.transpose();
  PMatrix3D R_rel = new PMatrix3D();
  R_rel.set(R_s);
  R_rel.apply(R_o);
  float tilt_X = atan2(R_rel.m21, R_rel.m22);
  float tilt_Y = atan2(-R_rel.m20, sqrt(sq(R_rel.m21) + sq(R_rel.m22)));
  float relRoll = atan2(R_rel.m10, R_rel.m00);

  PVector results = new PVector(tilt_X, -tilt_Y, relRoll);
  return results;
}

PMatrix3D getRotationMatrix(float roll, float pitch, float yaw) {
  PMatrix3D mat = new PMatrix3D();
  // Standard ZYX order: Yaw (Z), then Pitch (Y), then Roll (X)
  mat.rotateZ(yaw);
  mat.rotateY(pitch);
  mat.rotateX(roll);
  return mat;
}
