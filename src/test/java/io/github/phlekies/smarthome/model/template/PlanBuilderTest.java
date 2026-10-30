package io.github.phlekies.smarthome.model.template;

import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.door;
import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.frontDoor;
import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.window;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;

import org.junit.jupiter.api.Test;

import io.github.phlekies.smarthome.model.Wall;
import io.github.phlekies.smarthome.model.material.Materials;

class PlanBuilderTest {

    @Test
    void aDoorwayLeavesAGapAndAWindowBecomesGlass() {
        PlanBuilder plan = new PlanBuilder();
        plan.h(2, 0, 10, Materials.BRICK, 30, window(7, 2.0), door(3));

        List<Wall> walls = plan.walls();
        assertEquals(4, walls.size());
        assertSpan(walls.get(0), 0, 2.6);
        assertSpan(walls.get(1), 3.4, 6);
        assertSpan(walls.get(2), 6, 8);
        assertSpan(walls.get(3), 8, 10);
        assertSame(Materials.GLASS, walls.get(2).getMaterial());
        assertSame(Materials.BRICK, walls.get(3).getMaterial());
        assertEquals(30, walls.get(3).getThicknessCm());
        walls.forEach(wall -> assertEquals(2, wall.getY1()));
    }

    @Test
    void openingsMayReachTheEndsOfTheWall() {
        PlanBuilder plan = new PlanBuilder();
        plan.v(5, 0, 3, Materials.CONCRETE, 20, frontDoor(0.5), door(2.5, 1.0));

        List<Wall> walls = plan.walls();
        assertEquals(2, walls.size());
        assertSame(Materials.WOOD, walls.get(0).getMaterial());
        assertEquals(0, walls.get(0).getY1());
        assertEquals(1, walls.get(0).getY2());
        assertEquals(1, walls.get(1).getY1());
        assertEquals(2, walls.get(1).getY2());
    }

    @Test
    void originShiftsAndMirrorFlipsWallsAndRooms() {
        PlanBuilder plan = new PlanBuilder();
        plan.origin(10, 20);
        plan.mirror(4);
        plan.wall(1, 0, 3, 0, Materials.WOOD, 5);
        plan.room("Kitchen", 1, 2);

        Wall wall = plan.walls().getFirst();
        assertEquals(17, wall.getX1());
        assertEquals(15, wall.getX2());
        assertEquals(20, wall.getY1());
        assertEquals(new RoomLabel("Kitchen", 17, 22), plan.rooms().getFirst());
    }

    @Test
    void overlappingOrMisplacedOpeningsAreRejected() {
        PlanBuilder plan = new PlanBuilder();
        assertThrows(IllegalArgumentException.class,
                () -> plan.h(0, 0, 10, Materials.BRICK, 30, window(5, 2.0), door(6)));
        assertThrows(IllegalArgumentException.class, () -> plan.h(0, 0, 10, Materials.BRICK, 30, door(9.8)));
        assertThrows(IllegalArgumentException.class, () -> plan.v(0, 5, 1, Materials.BRICK, 30));
        assertThrows(IllegalArgumentException.class, () -> window(1, 0));
    }

    private static void assertSpan(Wall wall, double fromX, double toX) {
        assertEquals(fromX, wall.getX1(), 1e-9);
        assertEquals(toX, wall.getX2(), 1e-9);
    }
}
