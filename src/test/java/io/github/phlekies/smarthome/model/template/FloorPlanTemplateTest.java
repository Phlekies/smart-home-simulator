package io.github.phlekies.smarthome.model.template;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;

import io.github.phlekies.smarthome.app.SimulatorModel;
import io.github.phlekies.smarthome.model.Wall;
import io.github.phlekies.smarthome.model.material.Materials;
import io.github.phlekies.smarthome.physics.Geometry;

class FloorPlanTemplateTest {

    @ParameterizedTest
    @EnumSource(FloorPlanTemplate.class)
    void everyTemplateFitsInsideThePlan(FloorPlanTemplate template) {
        List<Wall> walls = template.walls();
        assertFalse(walls.isEmpty());
        for (Wall wall : walls) {
            for (double x : new double[] { wall.getX1(), wall.getX2() }) {
                assertTrue(x >= 0 && x <= SimulatorModel.PLAN_WIDTH_METERS, template + " x out of bounds: " + x);
            }
            for (double y : new double[] { wall.getY1(), wall.getY2() }) {
                assertTrue(y >= 0 && y <= SimulatorModel.PLAN_HEIGHT_METERS, template + " y out of bounds: " + y);
            }
            assertTrue(wall.length() > 0, template + " has a zero-length wall");
        }
    }

    @ParameterizedTest
    @EnumSource(FloorPlanTemplate.class)
    void everyTemplateIsDocumented(FloorPlanTemplate template) {
        assertFalse(template.displayName().isBlank());
        assertTrue(template.description().length() > 20);
    }

    @Test
    void namesAreUnique() {
        long distinct = Arrays.stream(FloorPlanTemplate.values()).map(FloorPlanTemplate::displayName).distinct().count();
        assertEquals(FloorPlanTemplate.values().length, distinct);
    }

    @Test
    void wallsAreFreshInstancesEveryTime() {
        Wall first = FloorPlanTemplate.HOTEL_FLOOR.walls().getFirst();
        Wall second = FloorPlanTemplate.HOTEL_FLOOR.walls().getFirst();
        assertNotSame(first, second);
        assertTrue(first.isEquivalentTo(second));
    }

    @Test
    void templatesAreScaledToRealisticSizes() {
        // The apartment is drawn 31 units wide and scaled by 1.3 → 40.3 m.
        Wall bottom = FloorPlanTemplate.TWO_BEDROOM_APARTMENT.walls().getFirst();
        assertEquals(40.3, bottom.length(), 1e-9);
    }

    @Test
    void housesAreDrawnToScale() {
        // The villa's south façade starts with a 2 m stretch of brick before the first window.
        Wall south = FloorPlanTemplate.MEDITERRANEAN_VILLA.walls().getFirst();
        assertEquals(2.0, south.length(), 1e-9);
        assertEquals(15.5, south.getX1(), 1e-9);
    }

    /**
     * Checks that the houses are complete, walkable homes. The plan is rasterised at 10 cm, with
     * every wall as thick as it really is, and flood-filled from its border: whatever the fill does
     * not reach is enclosed. Interior doors are gaps, so all the rooms of a home form one enclosed
     * region; only spaces behind a closed door or in another building add regions.
     */
    @Nested
    @DisplayName("Houses")
    class Houses {

        private static final double CELL = 0.1;

        /** Enclosed regions of each house: the home plus its garages, guest house or second home. */
        static final Map<FloorPlanTemplate, Integer> ENCLOSED_REGIONS = Map.of(
                FloorPlanTemplate.MEDITERRANEAN_VILLA, 2,
                FloorPlanTemplate.RANCH_HOUSE, 2,
                FloorPlanTemplate.COURTYARD_HOUSE, 1,
                FloorPlanTemplate.MODERN_GLASS_VILLA, 1,
                FloorPlanTemplate.NORDIC_TIMBER_HOUSE, 1,
                FloorPlanTemplate.STONE_FARMHOUSE, 2,
                FloorPlanTemplate.CONCRETE_BLOCK_HOUSE, 2,
                FloorPlanTemplate.VILLA_WITH_GUEST_HOUSE, 2,
                FloorPlanTemplate.SEMI_DETACHED_PAIR, 4,
                FloorPlanTemplate.TWO_WING_COUNTRY_HOUSE, 1);

        static List<FloorPlanTemplate> houses() {
            return Arrays.stream(FloorPlanTemplate.values()).filter(ENCLOSED_REGIONS::containsKey).toList();
        }

        @Test
        void theTenHousesAreTheTemplatesWithNamedRooms() {
            List<FloorPlanTemplate> named = Arrays.stream(FloorPlanTemplate.values())
                    .filter(template -> !template.rooms().isEmpty()).toList();
            assertEquals(houses(), named);
            assertEquals(10, named.size());
        }

        @ParameterizedTest
        @MethodSource("houses")
        void everyRoomCanBeWalkedIntoThroughTheDoors(FloorPlanTemplate house) {
            int[][] region = regions(house.walls());
            int enclosed = Arrays.stream(region).flatMapToInt(Arrays::stream).max().orElse(0) - 1;

            boolean[] named = new boolean[enclosed + 2];
            for (RoomLabel room : house.rooms()) {
                int label = region[cell(room.x())][cell(room.y())];
                assertTrue(label > 0, house + ": the label of " + room.name() + " lies on a wall");
                named[label] = true;
            }
            for (int id = 2; id < named.length; id++) {
                assertTrue(named[id], house + ": a sealed space has no room in it, near " + seedOf(region, id));
            }
            assertEquals(ENCLOSED_REGIONS.get(house), enclosed,
                    house + ": a room is sealed off or a closed door is missing");
        }

        @ParameterizedTest
        @MethodSource("houses")
        void wallsOnlyMeetAtTheirEnds(FloorPlanTemplate house) {
            List<Wall> walls = house.walls();
            for (int i = 0; i < walls.size(); i++) {
                for (int j = i + 1; j < walls.size(); j++) {
                    Wall a = walls.get(i);
                    Wall b = walls.get(j);
                    double[] hit = Geometry.segmentIntersection(a.getX1(), a.getY1(), a.getX2(), a.getY2(),
                            b.getX1(), b.getY1(), b.getX2(), b.getY2());
                    if (hit != null) {
                        assertFalse(isInside(hit[2]) && isInside(positionAlong(b, hit[0], hit[1])),
                                house + ": walls cross at " + point(hit[0], hit[1]));
                    }
                    assertTrue(collinearOverlap(a, b) < 1e-6,
                            house + ": walls overlap near " + point(a.getX1(), a.getY1()));
                }
            }
        }

        @ParameterizedTest
        @MethodSource("houses")
        void housesAreLargeWithWindowsAndAGarden(FloorPlanTemplate house) {
            List<Wall> walls = house.walls();
            int[][] region = regions(walls);
            long enclosedCells = Arrays.stream(region).flatMapToInt(Arrays::stream).filter(id -> id > 1).count();
            assertTrue(enclosedCells * CELL * CELL > 250, house + " is smaller than 250 m²");

            long windows = walls.stream().filter(wall -> wall.getMaterial() == Materials.GLASS).count();
            assertTrue(windows >= 10, house + " has only " + windows + " glazed openings");
            assertTrue(house.rooms().size() >= 10, house + " names only " + house.rooms().size() + " rooms");

            for (Wall wall : walls) {
                double minX = Math.min(wall.getX1(), wall.getX2());
                double maxX = Math.max(wall.getX1(), wall.getX2());
                double minY = Math.min(wall.getY1(), wall.getY2());
                double maxY = Math.max(wall.getY1(), wall.getY2());
                assertTrue(minX >= 3 && maxX <= SimulatorModel.PLAN_WIDTH_METERS - 3
                        && minY >= 3 && maxY <= SimulatorModel.PLAN_HEIGHT_METERS - 3,
                        house + " leaves less than 3 m of garden around it");
            }
        }

        /** Region id of every cell: 0 = wall, 1 = connected to the plan border, 2+ = enclosed. */
        private static int[][] regions(List<Wall> walls) {
            int nx = cell(SimulatorModel.PLAN_WIDTH_METERS);
            int ny = cell(SimulatorModel.PLAN_HEIGHT_METERS);
            int[][] region = new int[nx][ny];
            for (int i = 0; i < nx; i++) {
                for (int j = 0; j < ny; j++) {
                    region[i][j] = isWall(walls, (i + 0.5) * CELL, (j + 0.5) * CELL) ? 0 : -1;
                }
            }
            fill(region, 0, 0, 1);
            int next = 2;
            for (int i = 0; i < nx; i++) {
                for (int j = 0; j < ny; j++) {
                    if (region[i][j] == -1) {
                        fill(region, i, j, next++);
                    }
                }
            }
            return region;
        }

        /** A cell is solid if its centre lies within half the wall thickness (at least one cell). */
        private static boolean isWall(List<Wall> walls, double x, double y) {
            for (Wall wall : walls) {
                double halfThickness = Math.max(wall.getThicknessCm() / 200.0, 0.8 * CELL);
                if (Geometry.distancePointToSegment(x, y, wall.getX1(), wall.getY1(), wall.getX2(), wall.getY2())
                        <= halfThickness) {
                    return true;
                }
            }
            return false;
        }

        private static void fill(int[][] region, int startX, int startY, int id) {
            Deque<int[]> queue = new ArrayDeque<>();
            region[startX][startY] = id;
            queue.add(new int[] { startX, startY });
            while (!queue.isEmpty()) {
                int[] c = queue.poll();
                for (int[] n : new int[][] { { c[0] + 1, c[1] }, { c[0] - 1, c[1] }, { c[0], c[1] + 1 }, { c[0], c[1] - 1 } }) {
                    if (n[0] >= 0 && n[1] >= 0 && n[0] < region.length && n[1] < region[0].length
                            && region[n[0]][n[1]] == -1) {
                        region[n[0]][n[1]] = id;
                        queue.add(n);
                    }
                }
            }
        }

        private static int cell(double metres) {
            return (int) Math.floor(metres / CELL + 1e-9);
        }

        private static String seedOf(int[][] region, int id) {
            for (int i = 0; i < region.length; i++) {
                for (int j = 0; j < region[i].length; j++) {
                    if (region[i][j] == id) {
                        return point((i + 0.5) * CELL, (j + 0.5) * CELL);
                    }
                }
            }
            return "?";
        }

        private static boolean isInside(double t) {
            return t > 1e-6 && t < 1 - 1e-6;
        }

        private static double positionAlong(Wall wall, double x, double y) {
            double dx = wall.getX2() - wall.getX1();
            double dy = wall.getY2() - wall.getY1();
            return ((x - wall.getX1()) * dx + (y - wall.getY1()) * dy) / (dx * dx + dy * dy);
        }

        /** Length shared by two collinear walls (0 if they are not collinear). */
        private static double collinearOverlap(Wall a, Wall b) {
            double dx = a.getX2() - a.getX1();
            double dy = a.getY2() - a.getY1();
            double cross1 = dx * (b.getY1() - a.getY1()) - dy * (b.getX1() - a.getX1());
            double cross2 = dx * (b.getY2() - a.getY1()) - dy * (b.getX2() - a.getX1());
            if (Math.abs(cross1) > 1e-9 || Math.abs(cross2) > 1e-9) {
                return 0;
            }
            double s1 = positionAlong(a, b.getX1(), b.getY1());
            double s2 = positionAlong(a, b.getX2(), b.getY2());
            return (Math.min(1, Math.max(s1, s2)) - Math.max(0, Math.min(s1, s2))) * a.length();
        }

        private static String point(double x, double y) {
            return String.format(Locale.ROOT, "(%.1f, %.1f)", x, y);
        }
    }
}
