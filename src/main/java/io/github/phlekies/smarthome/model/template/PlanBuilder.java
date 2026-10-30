package io.github.phlekies.smarthome.model.template;

import static io.github.phlekies.smarthome.model.material.Materials.GLASS;
import static io.github.phlekies.smarthome.model.material.Materials.METAL_DOOR;
import static io.github.phlekies.smarthome.model.material.Materials.WOOD;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

import io.github.phlekies.smarthome.model.Wall;
import io.github.phlekies.smarthome.model.material.Material;

/**
 * Collects the walls of a template. Horizontal and vertical walls can have openings: a doorway
 * leaves a gap, while windows and closed doors become segments of their own material.
 */
final class PlanBuilder {

    private static final double EPSILON = 1e-9;

    /** An opening centred on a coordinate along the wall; a null material leaves a gap. */
    record Opening(double center, double width, Material material, double thicknessCm) {

        Opening {
            if (width <= 0) {
                throw new IllegalArgumentException("Opening width must be positive: " + width);
            }
        }

        /** Open interior doorway, 0.8 m wide. */
        static Opening door(double center) {
            return door(center, 0.8);
        }

        /** Open doorway or passage of the given width. */
        static Opening door(double center, double width) {
            return new Opening(center, width, null, 0.0);
        }

        /** Double-glazed window or glass sliding door. */
        static Opening window(double center, double width) {
            return new Opening(center, width, GLASS, 6.0);
        }

        /** Closed solid-wood entrance door. */
        static Opening frontDoor(double center) {
            return new Opening(center, 1.0, WOOD, 6.0);
        }

        /** Closed steel door: armoured entrance or fire door between a garage and the house. */
        static Opening metalDoor(double center) {
            return new Opening(center, 0.9, METAL_DOOR, 4.0);
        }

        /** Closed sectional garage door. */
        static Opening garageDoor(double center, double width) {
            return new Opening(center, width, METAL_DOOR, 4.0);
        }

        double start() {
            return center - width / 2.0;
        }

        double end() {
            return center + width / 2.0;
        }
    }

    /** A stretch of a wall: plain wall when {@code opening} is null. */
    private record Part(double start, double end, Opening opening) {
    }

    private final List<Wall> walls = new ArrayList<>();
    private final List<RoomLabel> rooms = new ArrayList<>();
    private double originX;
    private double originY;
    private double mirrorAxisX = Double.NaN;

    /** Walls and rooms added from now on are shifted by this offset, so a building is drawn around (0, 0). */
    void origin(double x, double y) {
        originX = x;
        originY = y;
    }

    /** Walls and rooms added from now on are mirrored across the vertical line {@code x = axisX} (before the origin shift). */
    void mirror(double axisX) {
        mirrorAxisX = axisX;
    }

    /** Names the room whose label is centred on {@code (x, y)}. */
    void room(String name, double x, double y) {
        rooms.add(new RoomLabel(name, toPlanX(x), originY + y));
    }

    void wall(double x1, double y1, double x2, double y2, Material material, double thicknessCm) {
        walls.add(new Wall(toPlanX(x1), originY + y1, toPlanX(x2), originY + y2, material, thicknessCm));
    }

    private double toPlanX(double x) {
        return originX + (Double.isNaN(mirrorAxisX) ? x : 2.0 * mirrorAxisX - x);
    }

    void rect(double x1, double y1, double x2, double y2, Material material, double thicknessCm) {
        wall(x1, y1, x2, y1, material, thicknessCm);
        wall(x2, y1, x2, y2, material, thicknessCm);
        wall(x2, y2, x1, y2, material, thicknessCm);
        wall(x1, y2, x1, y1, material, thicknessCm);
    }

    /** Horizontal wall at height {@code y} from {@code x1} to {@code x2}; openings are centred on an x. */
    void h(double y, double x1, double x2, Material material, double thicknessCm, Opening... openings) {
        for (Part part : split(x1, x2, openings)) {
            if (part.opening() == null) {
                wall(part.start(), y, part.end(), y, material, thicknessCm);
            } else {
                wall(part.start(), y, part.end(), y, part.opening().material(), part.opening().thicknessCm());
            }
        }
    }

    /** Vertical wall at {@code x} from {@code y1} to {@code y2}; openings are centred on a y. */
    void v(double x, double y1, double y2, Material material, double thicknessCm, Opening... openings) {
        for (Part part : split(y1, y2, openings)) {
            if (part.opening() == null) {
                wall(x, part.start(), x, part.end(), material, thicknessCm);
            } else {
                wall(x, part.start(), x, part.end(), part.opening().material(), part.opening().thicknessCm());
            }
        }
    }

    List<Wall> walls() {
        return walls;
    }

    List<RoomLabel> rooms() {
        return rooms;
    }

    /** Plain stretches and closed openings of {@code [from, to]} in order; doorways are left out. */
    private static List<Part> split(double from, double to, Opening... openings) {
        if (to - from <= EPSILON) {
            throw new IllegalArgumentException("Wall from " + from + " to " + to + " must run in increasing order");
        }
        Opening[] sorted = openings.clone();
        Arrays.sort(sorted, Comparator.comparingDouble(Opening::center));
        List<Part> parts = new ArrayList<>();
        double cursor = from;
        for (Opening opening : sorted) {
            if (opening.start() < cursor - EPSILON || opening.end() > to + EPSILON) {
                throw new IllegalArgumentException("Opening at " + opening.center() + " overlaps another one"
                        + " or does not fit in the wall from " + from + " to " + to);
            }
            if (opening.start() - cursor > EPSILON) {
                parts.add(new Part(cursor, opening.start(), null));
            }
            if (opening.material() != null) {
                parts.add(new Part(opening.start(), opening.end(), opening));
            }
            cursor = opening.end();
        }
        if (to - cursor > EPSILON) {
            parts.add(new Part(cursor, to, null));
        }
        return parts;
    }
}
