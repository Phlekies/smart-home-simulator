package io.github.phlekies.smarthome.model.template;

import static io.github.phlekies.smarthome.model.material.Materials.BRICK;
import static io.github.phlekies.smarthome.model.material.Materials.CONCRETE;
import static io.github.phlekies.smarthome.model.material.Materials.DRYWALL;
import static io.github.phlekies.smarthome.model.material.Materials.GLASS;
import static io.github.phlekies.smarthome.model.material.Materials.WOOD;
import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.door;
import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.frontDoor;
import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.garageDoor;
import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.metalDoor;
import static io.github.phlekies.smarthome.model.template.PlanBuilder.Opening.window;

/**
 * Single-storey houses drawn to scale, in metres, with x towards the east and y towards the
 * north. Wall coordinates are centre lines. Interior doors are drawn open (a gap in the wall);
 * entrance, garage and fire doors are closed.
 */
final class HousePlans {

    private HousePlans() {
    }

    /** Spanish chalet: brick cavity façades, hollow-brick partitions and an attached garage. */
    static void mediterraneanVilla(PlanBuilder plan) {
        plan.origin(15.5, 14);
        plan.h(0, 0, 26, BRICK, 30, window(3.5, 3.0), window(8.5, 2.0), window(13, 1.5), window(17, 1.5),
                window(22.5, 2.4));
        plan.v(26, 0, 12, BRICK, 30, window(3.3, 1.5), window(9.35, 1.0));
        plan.h(12, 0, 26, BRICK, 30, window(1.3, 1.0), window(5.3, 1.6), frontDoor(10), window(11.1, 0.6),
                window(13.25, 0.6), window(16.75, 1.5), window(24, 1.0));
        plan.v(0, 0, 5.5, BRICK, 30, window(2.75, 1.5));

        // Double garage on the west side, entered from the laundry through a fire door.
        plan.v(0, 5.5, 12, BRICK, 25, metalDoor(10.2));
        plan.h(12, -7, 0, BRICK, 30, garageDoor(-3.5, 5.0));
        plan.v(-7, 5.5, 12, BRICK, 30, window(8.75, 1.0));
        plan.h(5.5, -7, 0, BRICK, 30, frontDoor(-1.5));

        plan.h(5.5, 0, 8, BRICK, 10, door(5.3, 1.2));
        plan.h(5.5, 8, 19, BRICK, 10, door(9.6, 1.4), door(14.3), door(15.6));
        plan.h(6.7, 12, 19, BRICK, 10, door(13.25), door(15.4));
        plan.h(6.7, 19, 26, BRICK, 10, door(20.5), door(24));
        plan.v(19, 0, 12, BRICK, 10, door(6.1));
        plan.v(22, 6.7, 12, BRICK, 10, door(10));
        plan.v(11, 0, 5.5, BRICK, 10);
        plan.v(15, 0, 5.5, BRICK, 10);
        plan.v(2.6, 5.5, 12, BRICK, 10, door(7), door(10.2));
        plan.h(8.5, 0, 2.6, BRICK, 10);
        plan.v(8, 5.5, 12, BRICK, 10, door(9.5));
        plan.v(12, 6.7, 12, BRICK, 10, door(10.75));
        plan.h(9.5, 12, 14.5, BRICK, 10);
        plan.v(14.5, 6.7, 12, BRICK, 10);

        plan.room("Living-dining", 5.5, 2.75);
        plan.room("Kitchen", 5.3, 8.75);
        plan.room("Pantry", 1.3, 7);
        plan.room("Laundry", 1.3, 10.25);
        plan.room("Hall", 10, 9.3);
        plan.room("Bedroom 3", 13, 2.75);
        plan.room("Bedroom 2", 17, 2.75);
        plan.room("Master bedroom", 22.5, 3.3);
        plan.room("Bathroom", 13.25, 8.1);
        plan.room("WC", 13.25, 10.75);
        plan.room("Study", 16.75, 9.35);
        plan.room("Closet", 20.5, 9.35);
        plan.room("En-suite", 24, 9.35);
        plan.room("Garage", -3.5, 8.75);
    }

    /** American L-shaped ranch: brick veneer, drywall partitions and a three-car garage. */
    static void ranchHouse(PlanBuilder plan) {
        plan.origin(10, 11);
        plan.h(0, 0, 29.5, BRICK, 20, window(2.8, 1.6), window(7.1, 0.8), window(14, 2.4), window(18, 1.8),
                window(23, 1.8), window(27.5, 1.5));
        plan.v(0, 0, 11, BRICK, 20, window(2.4, 1.2), window(5.4, 0.8), window(8.5, 1.4));
        plan.h(11, 0, 20.5, BRICK, 20, window(2.2, 1.4), window(5.7, 0.8), window(9.1, 1.4), window(14.4, 1.8),
                frontDoor(19));
        plan.v(29.5, 0, 11, BRICK, 20, window(2.75, 1.4), window(6.25, 0.8), window(9, 1.4));

        // Three-car garage in front of the service wing; the laundry doubles as mudroom.
        plan.h(11, 20.5, 29.5, DRYWALL, 15, metalDoor(22.2));
        plan.v(20.5, 11, 18, BRICK, 20, frontDoor(16.5));
        plan.h(18, 20.5, 29.5, BRICK, 20, garageDoor(23.4, 4.8), garageDoor(27.6, 2.6));
        plan.v(29.5, 11, 18, BRICK, 20, window(14.5, 1.0));

        // Bedroom wing around a hallway that opens into the great room.
        plan.h(6, 0, 11.2, DRYWALL, 12, door(2.9), door(5.7), door(8.2));
        plan.h(4.8, 0, 11.2, DRYWALL, 12, door(4.6));
        plan.v(4.4, 6, 11, DRYWALL, 12);
        plan.v(7, 6, 11, DRYWALL, 12);
        plan.v(5.6, 0, 4.8, DRYWALL, 12, door(2.4));
        plan.v(8.6, 0, 4.8, DRYWALL, 12, door(2.4));
        plan.v(11.2, 0, 4.8, DRYWALL, 12);
        plan.v(11.2, 6, 11, DRYWALL, 12);

        plan.h(7.5, 11.2, 20.5, DRYWALL, 12, door(14.4, 3.6), door(19, 1.6));
        plan.v(17.5, 7.5, 11, DRYWALL, 12);

        plan.v(20.5, 0, 11, DRYWALL, 12, door(2.75, 2.4), door(6.25, 1.2));
        plan.h(5.5, 20.5, 29.5, DRYWALL, 12, door(27.2));
        plan.v(25.5, 0, 5.5, DRYWALL, 12);
        plan.h(7, 20.5, 29.5, DRYWALL, 12, door(22.2), door(25), door(26.8));
        plan.v(24, 7, 11, DRYWALL, 12);
        plan.v(26, 7, 11, DRYWALL, 12);

        plan.room("Master bedroom", 2.8, 2.4);
        plan.room("Bath", 7.1, 2.4);
        plan.room("Closet", 9.9, 2.4);
        plan.room("Bedroom 2", 2.2, 8.5);
        plan.room("Bath", 5.7, 8.5);
        plan.room("Bedroom 3", 9.1, 8.5);
        plan.room("Great room", 15.8, 3.75);
        plan.room("Kitchen", 14.4, 9.25);
        plan.room("Foyer", 19, 9.25);
        plan.room("Dining", 23, 2.75);
        plan.room("Office", 27.5, 2.75);
        plan.room("Laundry", 22.25, 9);
        plan.room("WC", 25, 9);
        plan.room("Guest room", 27.75, 9);
        plan.room("Garage", 25, 14.5);
    }

    /** Andalusian patio house: thick load-bearing brick and a glazed gallery around the courtyard. */
    static void courtyardHouse(PlanBuilder plan) {
        plan.origin(14, 9);
        plan.h(0, 0, 22, BRICK, 40, window(3, 1.4), window(6.5, 1.4), frontDoor(11), window(15, 1.4),
                window(19.6, 1.2));
        plan.v(22, 0, 22, BRICK, 40, window(2.8, 1.2), window(7, 0.8), window(9.7, 0.6), window(13.7, 1.4),
                window(19.2, 1.6));
        plan.h(22, 0, 22, BRICK, 40, window(4.4, 1.6), window(8.2, 0.8), window(11.4, 1.6), window(14.3, 0.8),
                window(18.7, 2.0));
        plan.v(0, 0, 22, BRICK, 40, window(2.8, 1.4), window(7.1, 1.2), window(9.8, 0.6), window(13.7, 1.4),
                window(17.7, 0.6), window(20.5, 1.2));

        // Load-bearing ring between the rooms and the gallery.
        plan.h(5.6, 5.6, 16.4, BRICK, 25, door(7.6, 1.2), door(11, 1.6), door(14.5, 1.2));
        plan.h(16.4, 5.6, 16.4, BRICK, 25, door(6.2), door(8.2), door(11.4), door(15.9));
        plan.v(5.6, 5.6, 16.4, BRICK, 25, door(7.1), door(9.8), door(13.7));
        plan.v(16.4, 5.6, 16.4, BRICK, 25, door(7), door(9.7), door(12));

        // Glazed gallery around the open-air courtyard.
        plan.h(7, 7, 15, GLASS, 6, door(11, 1.6));
        plan.h(15, 7, 15, GLASS, 6, door(11, 1.6));
        plan.v(7, 7, 15, GLASS, 6);
        plan.v(15, 7, 15, GLASS, 6);

        plan.h(5.6, 0, 5.6, BRICK, 12);
        plan.h(5.6, 16.4, 22, BRICK, 12, door(19.2));
        plan.h(16.4, 0, 5.6, BRICK, 12);
        plan.h(16.4, 16.4, 22, BRICK, 12);
        plan.v(9.5, 0, 5.6, BRICK, 12);
        plan.v(12.5, 0, 5.6, BRICK, 12);
        plan.v(17.2, 0, 5.6, BRICK, 12, door(2.8, 0.9));
        plan.h(8.4, 16.4, 22, BRICK, 12);
        plan.h(11, 16.4, 22, BRICK, 12);
        plan.h(8.6, 0, 5.6, BRICK, 12);
        plan.h(11, 0, 5.6, BRICK, 12);
        plan.v(6.8, 16.4, 22, BRICK, 12);
        plan.v(9.6, 16.4, 22, BRICK, 12);
        plan.v(13.2, 16.4, 22, BRICK, 12);
        plan.v(15.4, 16.4, 22, BRICK, 12, door(19.2));
        plan.v(3, 16.4, 19, BRICK, 12, door(17.7));
        plan.h(19, 0, 3, BRICK, 12);

        plan.room("Living room", 4.75, 2.8);
        plan.room("Entrance", 11, 2.8);
        plan.room("Dining", 14.85, 2.8);
        plan.room("Kitchen", 19.6, 2.8);
        plan.room("Laundry", 19.2, 7);
        plan.room("Bathroom", 19.2, 9.7);
        plan.room("Bedroom 3", 19.2, 13.7);
        plan.room("TV room", 2.8, 7.1);
        plan.room("Bathroom", 2.8, 9.8);
        plan.room("Guest room", 2.8, 13.7);
        plan.room("Bedroom 2", 4.9, 20.5);
        plan.room("Bath", 1.5, 17.7);
        plan.room("Bathroom", 8.2, 19.2);
        plan.room("Study", 11.4, 19.2);
        plan.room("Bath", 14.3, 19.2);
        plan.room("Master bedroom", 18.7, 19.2);
        plan.room("Courtyard", 11, 11);
    }

    /** T-shaped contemporary villa: concrete walls, glass curtain walls and an open-plan day wing. */
    static void modernGlassVilla(PlanBuilder plan) {
        plan.origin(13, 5);
        // Day wing: glazed towards the garden, with a laundry and a WC in concrete boxes.
        plan.h(0, 0, 24, CONCRETE, 25, window(4, 7.0), window(12, 7.0), window(20, 7.0));
        plan.v(0, 0, 9, CONCRETE, 25, window(2.75, 3.5), window(7.25, 0.6));
        plan.v(24, 0, 9, CONCRETE, 25, window(4.5, 6.0));
        plan.h(9, 0, 8, CONCRETE, 25, window(5.5, 2.4));
        plan.h(9, 16, 24, CONCRETE, 25, window(20, 4.0));
        plan.h(5.5, 0, 3.5, CONCRETE, 20);
        plan.v(3.5, 5.5, 9, CONCRETE, 20, door(7.25));
        plan.h(6.5, 16, 18.5, CONCRETE, 20);
        plan.v(16, 6.5, 9, CONCRETE, 20);
        plan.v(18.5, 6.5, 9, CONCRETE, 20, door(7.75));
        plan.v(12, 2.5, 5.5, CONCRETE, 25);

        // Night wing: hall and cinema, then a glazed gallery serving the bedrooms.
        plan.h(9, 8, 12.5, DRYWALL, 10, door(10.25, 2.0));
        plan.h(9, 12.5, 16, CONCRETE, 20);
        plan.v(8, 9, 30, CONCRETE, 25, frontDoor(11.25), window(19, 10.6), window(27.25, 3.0));
        plan.v(16, 9, 30, CONCRETE, 25, window(15.5, 2.4), window(18.75, 0.8), window(22.25, 2.4),
                window(28.5, 0.8));
        plan.h(30, 8, 16, CONCRETE, 25, window(10.25, 3.5), window(14.25, 0.8));
        plan.v(12.5, 9, 13.5, CONCRETE, 20, door(12.6));
        plan.h(13.5, 8, 12.5, DRYWALL, 10, door(8.8, 1.4));
        plan.h(13.5, 12.5, 16, CONCRETE, 20);
        plan.v(9.6, 13.5, 24.5, DRYWALL, 10, door(14.4), door(18.75), door(21));
        plan.h(17.5, 9.6, 16, DRYWALL, 10);
        plan.h(20, 9.6, 16, DRYWALL, 10);
        plan.h(24.5, 8, 16, DRYWALL, 10, door(8.8));
        plan.v(12.5, 24.5, 30, DRYWALL, 10, door(25.75), door(28.5));
        plan.h(27, 12.5, 16, DRYWALL, 10);

        plan.room("Kitchen", 5, 3.5);
        plan.room("Laundry", 1.75, 7.25);
        plan.room("Dining", 9.5, 4);
        plan.room("Living room", 19, 4);
        plan.room("WC", 17.25, 7.75);
        plan.room("Hall", 10.25, 11.25);
        plan.room("Cinema", 14.25, 11.25);
        plan.room("Bedroom 2", 12.8, 15.5);
        plan.room("Bathroom", 12.8, 18.75);
        plan.room("Bedroom 3", 12.8, 22.25);
        plan.room("Master bedroom", 10.25, 27.25);
        plan.room("Closet", 14.25, 25.75);
        plan.room("En-suite", 14.25, 28.5);
    }

    /** Scandinavian longhouse: timber walls, open-plan day zone and a sauna next to the bathroom. */
    static void nordicTimberHouse(PlanBuilder plan) {
        plan.origin(8, 15);
        plan.h(0, 0, 34, WOOD, 30, window(2.5, 2.4), window(6, 2.4), window(11.25, 3.0), window(16, 2.0),
                window(20, 1.8), window(24, 1.8), window(28.5, 2.4), window(32, 2.4));
        plan.v(0, 0, 10, WOOD, 30, window(3.25, 3.0), window(8.25, 1.2));
        plan.h(10, 0, 34, WOOD, 30, window(2.25, 1.6), window(7.75, 2.4), window(12.5, 0.8), frontDoor(16),
                window(17.2, 0.5), window(19.75, 0.8), window(25.5, 0.8), window(32, 0.8));
        plan.v(34, 0, 10, WOOD, 30, window(2.75, 2.0), window(7.75, 0.8));

        // Open-plan day zone with a free-standing masonry fireplace.
        plan.v(8.5, 2, 4, BRICK, 40);
        plan.h(6.5, 0, 14, DRYWALL, 12, door(2.25), door(7.75, 5.0), door(12.5));
        plan.v(4.5, 6.5, 10, DRYWALL, 12);
        plan.v(11, 6.5, 10, DRYWALL, 12);
        plan.v(14, 0, 10, DRYWALL, 12, door(6));

        // Night zone: bedrooms to the south, bathroom, sauna and laundry to the north.
        plan.h(5.5, 14, 34, DRYWALL, 12, door(16), door(20.8), door(24.8), door(27), door(32));
        plan.h(6.8, 18, 30, DRYWALL, 12, door(19.75), door(25.5), door(28.5));
        plan.v(18, 0, 5.5, DRYWALL, 12);
        plan.v(18, 6.8, 10, DRYWALL, 12);
        plan.v(22, 0, 5.5, DRYWALL, 12);
        plan.v(26, 0, 5.5, DRYWALL, 12);
        plan.v(21.5, 6.8, 10, WOOD, 12, door(8.4));
        plan.v(24, 6.8, 10, WOOD, 12);
        plan.v(27, 6.8, 10, DRYWALL, 12);
        plan.v(30, 5.5, 10, DRYWALL, 12);

        plan.room("Living room", 4, 3.25);
        plan.room("Kitchen", 11.25, 3.25);
        plan.room("Dining", 7.75, 8.25);
        plan.room("Den", 2.25, 8.25);
        plan.room("Pantry", 12.5, 8.25);
        plan.room("Hall", 16, 7.75);
        plan.room("Office", 16, 2.75);
        plan.room("Bedroom 2", 20, 2.75);
        plan.room("Bedroom 3", 24, 2.75);
        plan.room("Master bedroom", 30, 2.75);
        plan.room("Bathroom", 19.75, 8.4);
        plan.room("Sauna", 22.75, 8.4);
        plan.room("Laundry", 25.5, 8.4);
        plan.room("Closet", 28.5, 8.4);
        plan.room("En-suite", 32, 7.75);
    }

    /** U-shaped stone farmhouse around a walled yard, with a glazed gallery and a converted barn. */
    static void stoneFarmhouse(PlanBuilder plan) {
        plan.origin(10, 8);
        // 50 cm stone walls (modelled as concrete) and a lower wall closing the yard.
        plan.h(0, 0, 30, CONCRETE, 50, window(2, 1.2), window(4.75, 1.2), window(9.25, 1.4), window(14, 1.6),
                window(18, 1.4), window(21, 1.4), window(26.5, 1.4));
        plan.v(0, 0, 24, CONCRETE, 50, window(4, 1.2), window(10, 1.2), window(13.25, 0.6), window(16.5, 1.2),
                window(20, 0.6), window(22.75, 1.4));
        plan.h(24, 0, 8, CONCRETE, 50, window(5, 1.4));
        plan.v(8, 8, 24, CONCRETE, 50, window(10.6, 4.0), window(15.4, 4.0), window(21.25, 1.6));
        plan.h(8, 8, 23, CONCRETE, 50, window(10.25, 3.5), frontDoor(14), window(18, 4.0), window(21.75, 1.5));
        plan.v(23, 8, 24, CONCRETE, 50, window(11, 1.6), window(19, 1.0));
        plan.v(30, 0, 24, CONCRETE, 50, window(2.5, 1.4), frontDoor(6.5), window(11, 1.6));
        plan.h(24, 23, 30, CONCRETE, 50, garageDoor(26.5, 3.5));
        plan.h(24, 8, 23, CONCRETE, 40, door(15.5, 3.0));

        // Load-bearing brick behind the gallery and around the central hall.
        plan.h(6.5, 6.5, 23, BRICK, 30, door(9.25, 1.0), door(14, 1.6), door(19.5, 1.0));
        plan.v(6.5, 0, 18.5, BRICK, 30, door(3.25, 1.2), door(7.25), door(9.5), door(13.25), door(15.5));
        plan.h(8, 0, 6.5, BRICK, 30);
        plan.v(12, 0, 6.5, BRICK, 30, door(3.25, 1.2));
        plan.v(16, 0, 6.5, BRICK, 30, door(3.25, 1.6));
        plan.v(23, 0, 8, BRICK, 30, door(7.25));
        plan.h(8, 23, 30, BRICK, 30, door(26.5));
        plan.h(14, 23, 30, BRICK, 30, metalDoor(24.5));

        plan.h(12, 0, 6.5, BRICK, 12);
        plan.h(14.5, 0, 6.5, BRICK, 12);
        plan.h(18.5, 0, 8, BRICK, 12, door(7.25));
        plan.v(3.5, 18.5, 21.5, BRICK, 12, door(20));
        plan.h(21.5, 0, 3.5, BRICK, 12);
        plan.h(5, 23, 30, BRICK, 12, door(26.5));

        plan.room("Kitchen", 3.25, 4);
        plan.room("Dining", 9.25, 3.25);
        plan.room("Hall", 14, 3.25);
        plan.room("Living room", 19.5, 3.25);
        plan.room("Office", 26.5, 2.5);
        plan.room("Boot room", 26.5, 6.5);
        plan.room("Workshop", 26.5, 11);
        plan.room("Garage", 26.5, 19);
        plan.room("Bedroom 2", 3.25, 10);
        plan.room("Bathroom", 3.25, 13.25);
        plan.room("Bedroom 3", 3.25, 16.5);
        plan.room("Master bedroom", 5.25, 22.75);
        plan.room("En-suite", 1.75, 20);
        plan.room("Yard", 15.5, 16);
    }

    /** Deep-plan family house in concrete block, with an open great room and an internal garage. */
    static void concreteBlockHouse(PlanBuilder plan) {
        plan.origin(12, 10.5);
        plan.h(0, 0, 26, CONCRETE, 20, window(3.5, 2.4), window(10, 3.0), window(15, 3.0), window(22.5, 3.0));
        plan.v(0, 0, 19, CONCRETE, 20, window(3.25, 1.6), window(9, 0.8), window(12.2, 0.8), window(16, 1.4));
        plan.h(19, 0, 26, CONCRETE, 20, window(2.25, 1.4), window(6, 0.6), window(9.75, 1.4), window(12.85, 0.5),
                frontDoor(13.75), window(14.65, 0.5), window(17.25, 1.4), garageDoor(22.5, 5.0));
        plan.v(26, 0, 19, CONCRETE, 20, window(3.25, 2.4), window(9, 1.0), frontDoor(15));

        plan.h(6.5, 0, 26, DRYWALL, 12, door(2), door(5.5), door(9.5, 3.0), door(15.5, 4.0), door(24));
        plan.h(11.5, 0, 19, DRYWALL, 12, door(9.5, 2.4), door(15.5, 1.6));
        plan.h(12.9, 0, 19, DRYWALL, 12, door(3.5), door(6), door(8.5), door(13.75, 2.0), door(17.5));
        plan.v(7, 0, 6.5, DRYWALL, 12, door(5.5, 0.9));
        plan.v(7, 6.5, 11.5, DRYWALL, 12);
        plan.v(4, 6.5, 11.5, DRYWALL, 12);
        plan.v(12, 6.5, 11.5, DRYWALL, 12, door(9, 2.0));
        plan.v(19, 0, 6.5, DRYWALL, 12, door(3.25, 3.0));
        plan.v(19, 6.5, 11.5, DRYWALL, 12, door(9));
        plan.v(21, 6.5, 11.5, DRYWALL, 12);
        plan.v(4.5, 12.9, 19, DRYWALL, 12);
        plan.v(7.5, 12.9, 19, DRYWALL, 12);
        plan.v(12, 12.9, 19, DRYWALL, 12);
        plan.v(15.5, 12.9, 19, DRYWALL, 12);

        // Garage separated by block walls and a fire door from the laundry.
        plan.h(11.5, 19, 26, CONCRETE, 20, metalDoor(23.5));
        plan.v(19, 11.5, 19, CONCRETE, 20);

        plan.room("Master bedroom", 3.5, 3.25);
        plan.room("Great room", 13, 3.25);
        plan.room("Family room", 22.5, 3.25);
        plan.room("Master bath", 2, 9);
        plan.room("Closet", 5.5, 9);
        plan.room("Dining", 9.5, 9);
        plan.room("Kitchen", 15.5, 9);
        plan.room("Pantry", 20, 9);
        plan.room("Laundry", 23.5, 9);
        plan.room("Bedroom 2", 2.25, 16);
        plan.room("Bath", 6, 16);
        plan.room("Bedroom 3", 9.75, 16);
        plan.room("Foyer", 13.75, 16);
        plan.room("Study", 17.25, 16);
        plan.room("Garage", 22.5, 15.25);
    }

    /** Villa with a detached guest studio across the pool terrace. */
    static void villaWithGuestHouse(PlanBuilder plan) {
        plan.origin(5.5, 13);
        plan.h(0, 0, 22, BRICK, 25, window(2.5, 3.0), window(6.75, 2.0), window(11.5, 2.4), window(16.5, 1.6),
                window(20.5, 0.8));
        plan.v(0, 0, 13, BRICK, 25, window(3.25, 1.6), window(7.15, 0.8), window(10.4, 1.4));
        plan.h(13, 0, 22, BRICK, 25, window(2, 1.4), window(5.3, 0.6), window(8.6, 1.4), frontDoor(12.3),
                window(16.75, 1.8), window(20.75, 0.6));
        plan.v(22, 0, 13, BRICK, 25, frontDoor(1.75), window(11.25, 0.6));

        plan.v(9, 0, 6.5, BRICK, 10, door(3.25, 3.5));
        plan.v(14, 0, 6.5, BRICK, 10, door(4.5, 1.0));
        plan.v(19, 0, 6.5, BRICK, 10, door(1.75), door(5));
        plan.h(3.5, 19, 22, BRICK, 10);
        plan.h(6.5, 0, 22, BRICK, 10, door(4.5, 1.2), door(11.5, 2.4));
        plan.h(7.8, 0, 10.6, BRICK, 10, door(2), door(5.3), door(8.6));
        plan.v(4, 7.8, 13, BRICK, 10);
        plan.v(6.6, 7.8, 13, BRICK, 10);
        plan.v(10.6, 7.8, 13, BRICK, 10);
        plan.v(14, 6.5, 13, BRICK, 10, door(10.5));
        plan.v(19.5, 6.5, 13, BRICK, 10, door(8), door(11.25));
        plan.h(9.5, 19.5, 22, BRICK, 10);

        // Guest studio on the far side of the pool.
        plan.h(0, 30, 39, BRICK, 25, window(32, 2.4), window(37.5, 0.6));
        plan.v(30, 0, 7, BRICK, 25, window(2.5, 1.4), frontDoor(5.5));
        plan.h(7, 30, 39, BRICK, 25, window(33, 1.6), window(37.5, 1.0));
        plan.v(39, 0, 7, BRICK, 25, window(5.25, 1.2));
        plan.v(36, 0, 7, DRYWALL, 10, door(1.75), door(5.25, 1.6));
        plan.h(3.5, 36, 39, DRYWALL, 10);

        plan.room("Living room", 4.5, 3.25);
        plan.room("Dining", 11.5, 3.25);
        plan.room("Kitchen", 16.5, 3.25);
        plan.room("Utility", 20.5, 1.75);
        plan.room("Pantry", 20.5, 5);
        plan.room("Bedroom 2", 2, 10.4);
        plan.room("Bath", 5.3, 10.4);
        plan.room("Bedroom 3", 8.6, 10.4);
        plan.room("Hall", 12.3, 10.4);
        plan.room("Master bedroom", 16.75, 9.75);
        plan.room("Closet", 20.75, 8);
        plan.room("En-suite", 20.75, 11.25);
        plan.room("Pool", 26, 3.5);
        plan.room("Guest studio", 33, 3.5);
        plan.room("Bath", 37.5, 1.75);
        plan.room("Kitchen", 37.5, 5.25);
    }

    /** Two mirrored homes sharing a concrete party wall, each with its own garage. */
    static void semiDetachedPair(PlanBuilder plan) {
        plan.origin(9, 12.7);
        plan.v(16, 0, 14.6, CONCRETE, 25);
        semiDetachedHome(plan);
        plan.mirror(16);
        semiDetachedHome(plan);
    }

    /** The western home of the pair; the party wall runs along x = 16. */
    private static void semiDetachedHome(PlanBuilder plan) {
        plan.h(0, 0, 16, BRICK, 30, window(2.6, 1.6), window(8, 3.0), window(13, 3.0));
        plan.v(0, 0, 14.6, BRICK, 30, window(2.4, 1.4), window(6.1, 0.6), window(8, 0.8), window(11.6, 1.4));
        plan.h(14.6, 0, 16, BRICK, 30, window(2, 1.4), window(5.2, 0.6), window(8.1, 1.4), frontDoor(11),
                garageDoor(14.1, 2.8));

        plan.h(7.4, 0, 12.2, BRICK, 10, door(3.9), door(8.7, 3.0));
        plan.h(7.4, 12.2, 16, BRICK, 25);
        plan.h(8.6, 0, 9.8, BRICK, 10, door(2), door(5.2), door(8.1));
        plan.v(4, 8.6, 14.6, BRICK, 10);
        plan.v(6.4, 8.6, 14.6, BRICK, 10);
        plan.v(9.8, 8.6, 14.6, BRICK, 10);
        plan.v(12.2, 7.4, 14.6, BRICK, 25, metalDoor(11.5));
        plan.v(5.2, 0, 7.4, BRICK, 10);
        plan.h(4.8, 0, 5.2, BRICK, 10, door(3.9));
        plan.v(2.6, 4.8, 7.4, BRICK, 10, door(6.1));

        plan.room("Master bedroom", 2.6, 2.4);
        plan.room("Bath", 1.3, 6.1);
        plan.room("Closet", 3.9, 6.1);
        plan.room("Living-kitchen", 10.6, 3.7);
        plan.room("Bedroom 2", 2, 11.6);
        plan.room("Bath", 5.2, 11.6);
        plan.room("Bedroom 3", 8.1, 11.6);
        plan.room("Hall", 11, 11.6);
        plan.room("Garage", 14.1, 11);
    }

    /** Country house with a day wing and a night wing joined by a glass entrance gallery. */
    static void twoWingCountryHouse(PlanBuilder plan) {
        plan.origin(13, 9);
        // Day wing.
        plan.h(0, 0, 9, BRICK, 35, window(2.5, 2.4), window(6.5, 2.4));
        plan.v(0, 0, 22, BRICK, 35, window(4, 2.4), window(10.75, 1.6), window(16, 1.6), window(20.25, 0.8));
        plan.h(22, 0, 9, BRICK, 35, window(4.5, 0.8), frontDoor(7.5));
        plan.v(9, 0, 22, BRICK, 35, window(4, 2.4), door(10.5, 5.0), window(16, 1.6));
        plan.h(8, 0, 9, BRICK, 12, door(2.75, 2.4), door(7.25, 1.6));
        plan.v(5.5, 8, 13.5, BRICK, 12, door(10.75, 1.2));
        plan.h(13.5, 0, 9, BRICK, 12, door(2.75, 1.0), door(7.25, 1.0));
        plan.h(18.5, 0, 9, BRICK, 12, door(1.5), door(4.5), door(7.5));
        plan.v(3, 18.5, 22, BRICK, 12);
        plan.v(6, 18.5, 22, BRICK, 12);

        // Glass gallery with the main entrance.
        plan.h(8, 9, 16, GLASS, 6);
        plan.h(13, 9, 16, GLASS, 6, frontDoor(12.5));

        // Night wing.
        plan.h(0, 16, 24, BRICK, 35, window(18.5, 2.4));
        plan.v(24, 0, 22, BRICK, 35, window(5.25, 0.8), window(9, 1.6), window(12.25, 0.8), window(15.5, 1.6),
                window(19.75, 1.6));
        plan.h(22, 16, 24, BRICK, 35, window(16.65, 0.6), window(20.65, 1.6));
        plan.v(16, 0, 22, BRICK, 35, window(3.5, 2.4), door(10.5, 5.0), window(15.5, 2.0), window(19.5, 2.0));
        plan.h(7, 16, 24, DRYWALL, 12, door(16.65));
        plan.v(21, 0, 7, DRYWALL, 12, door(1.75), door(5.25));
        plan.h(3.5, 21, 24, DRYWALL, 12);
        plan.v(17.3, 7, 22, DRYWALL, 12, door(9), door(12.25), door(14.5), door(18.5));
        plan.h(11, 17.3, 24, DRYWALL, 12);
        plan.h(13.5, 17.3, 24, DRYWALL, 12);
        plan.h(17.5, 17.3, 24, DRYWALL, 12);

        plan.room("Living room", 4.5, 4);
        plan.room("Dining", 2.75, 10.75);
        plan.room("Hall", 7.25, 10.75);
        plan.room("Kitchen", 4.5, 16);
        plan.room("Pantry", 1.5, 20.25);
        plan.room("Laundry", 4.5, 20.25);
        plan.room("Mudroom", 7.5, 20.25);
        plan.room("Gallery", 12.5, 10.5);
        plan.room("Master bedroom", 18.5, 3.5);
        plan.room("Closet", 22.5, 1.75);
        plan.room("En-suite", 22.5, 5.25);
        plan.room("Bedroom 2", 20.65, 9);
        plan.room("Bath", 20.65, 12.25);
        plan.room("Bedroom 3", 20.65, 15.5);
        plan.room("Bedroom 4", 20.65, 19.75);
    }
}
