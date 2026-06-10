import cv2
import time

from config import parse_args

from calibration import (
    load_camera_calibration
)

from camera import (
    create_camera
)

from aruco_detector import (
    create_detector,
    detect_markers
)

from pose import (
    estimate_pose
)

from marker import (
    build_marker_data
)

from osc_sender import (
    OscSender
)

from visualization import (
    draw_markers,
    draw_fps,
    draw_axes
)

from filters.marker_filter_manager import (
    MarkerFilterManager
)


def main():

    args = parse_args()

    camera_matrix, dist_coeffs = \
        load_camera_calibration()

    cap = create_camera(
        args.cam,
        args.width,
        args.height,
        args.win
    )

    detector = create_detector(
        args.pattern
    )

    osc = OscSender()

    filter_manager = (
        MarkerFilterManager()
    )

    prev = time.time()

    while True:

        ret, frame = cap.read()

        if not ret:
            continue

        if args.flip:
            frame = cv2.flip(
                frame,
                -1
            )

        corners, ids, _ = detect_markers(
            detector,
            frame
        )

        now = time.time()

        fps = 1.0 / (
            now - prev + 1e-6
        )

        prev = now

        rvecs, tvecs = None, None
        if ids is not None:

            rvecs, tvecs, _ = estimate_pose(
                corners,
                args.size,
                camera_matrix,
                dist_coeffs
            )

            for i in range(len(ids)):

                marker = build_marker_data(
                    ids[i][0],
                    corners[i][0],
                    rvecs[i],
                    tvecs[i]
                )

                #
                # Coordinate smoothing
                #
                marker = (
                    filter_manager.process(
                        marker,
                        now
                    )
                )

                osc.send_marker(
                    marker
                )

        draw_markers(
            frame,
            corners,
            ids
        )

        draw_axes(
            frame,
            camera_matrix,
            dist_coeffs,
            rvecs,
            tvecs,
            args.size
        )

        draw_fps(
            frame,
            fps
        )

        cv2.imshow(
            "server",
            frame
        )

        if (
            cv2.waitKey(1)
            & 0xFF
            == ord("q")
        ):
            break

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()