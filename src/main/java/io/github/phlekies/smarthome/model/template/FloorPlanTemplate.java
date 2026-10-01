package io.github.phlekies.smarthome.model.template;

import static io.github.phlekies.smarthome.model.material.Materials.BRICK;
import static io.github.phlekies.smarthome.model.material.Materials.CONCRETE;
import static io.github.phlekies.smarthome.model.material.Materials.DRYWALL;
import static io.github.phlekies.smarthome.model.material.Materials.GLASS;
import static io.github.phlekies.smarthome.model.material.Materials.METAL_DOOR;
import static io.github.phlekies.smarthome.model.material.Materials.WOOD;

import java.util.List;
import java.util.function.Consumer;

import io.github.phlekies.smarthome.model.Wall;

/**
 * Built-in indoor floor plans. The original layouts are drawn on a compact grid and enlarged to
 * realistic sizes; the houses are drawn to scale, with doorways, windows and named rooms.
 */
public enum FloorPlanTemplate {

    COMPACT_STUDIO("Compact studio",
            "Small home with an open living area, bathroom and a partially separated bedroom.",
            plan -> {
                plan.rect(2, 2, 24, 18, CONCRETE, 15);
                plan.wall(18, 9, 18, 18, DRYWALL, 8);
                plan.wall(18, 9, 24, 9, DRYWALL, 8);
                plan.wall(10, 12, 18, 12, WOOD, 6);
                plan.wall(10, 12, 10, 18, WOOD, 6);
                plan.wall(5, 8, 15, 8, WOOD, 5);
                plan.wall(7, 2, 7, 8, WOOD, 5);
            }),

    TWO_BEDROOM_APARTMENT("Two-bedroom apartment",
            "City apartment with living room, kitchen, two bedrooms and a central bathroom core.",
            plan -> {
                plan.rect(1, 1, 32, 22, BRICK, 12);
                plan.wall(12, 1, 12, 15, DRYWALL, 8);
                plan.wall(22, 7, 22, 22, DRYWALL, 8);
                plan.wall(1, 15, 12, 15, DRYWALL, 8);
                plan.wall(12, 7, 22, 7, DRYWALL, 8);
                plan.wall(12, 15, 22, 15, DRYWALL, 8);
                plan.wall(17, 7, 17, 15, WOOD, 6);
                plan.wall(26, 1, 26, 7, WOOD, 6);
            }),

    HOUSE_WITH_CORRIDOR("House with corridor",
            "Rectangular family house with a main corridor and rooms on both sides.",
            plan -> {
                plan.rect(1, 1, 33, 27, CONCRETE, 16);
                plan.wall(1, 14, 33, 14, BRICK, 10);
                plan.wall(17, 14, 17, 27, BRICK, 10);
                plan.wall(9, 14, 9, 27, DRYWALL, 8);
                plan.wall(25, 14, 25, 27, DRYWALL, 8);
                plan.wall(11, 1, 11, 14, DRYWALL, 8);
                plan.wall(23, 1, 23, 14, DRYWALL, 8);
                plan.wall(11, 8, 23, 8, WOOD, 6);
            }),

    L_SHAPED_HOUSE("L-shaped house",
            "L-shaped plan with a social wing and a private wing; good for testing corners and shadow zones.",
            plan -> {
                plan.wall(2, 2, 27, 2, CONCRETE, 16);
                plan.wall(27, 2, 27, 12, CONCRETE, 16);
                plan.wall(27, 12, 33, 12, CONCRETE, 16);
                plan.wall(33, 12, 33, 28, CONCRETE, 16);
                plan.wall(12, 28, 33, 28, CONCRETE, 16);
                plan.wall(12, 22, 12, 28, CONCRETE, 16);
                plan.wall(2, 22, 12, 22, CONCRETE, 16);
                plan.wall(2, 2, 2, 22, CONCRETE, 16);
                plan.wall(12, 12, 27, 12, DRYWALL, 8);
                plan.wall(18, 2, 18, 12, DRYWALL, 8);
                plan.wall(8, 2, 8, 22, WOOD, 6);
                plan.wall(12, 18, 33, 18, DRYWALL, 8);
                plan.wall(22, 18, 22, 28, DRYWALL, 8);
            }),

    MEDITERRANEAN_VILLA("Mediterranean villa",
            "Single-storey Spanish villa: brick façades, living-dining room facing the garden, three"
                    + " bedrooms, a study, two bathrooms and a double garage.",
            Units.METRES, HousePlans::mediterraneanVilla),

    RANCH_HOUSE("Ranch house",
            "L-shaped American ranch: brick veneer, drywall partitions, open great room, four bedrooms"
                    + " and a three-car garage.",
            Units.METRES, HousePlans::ranchHouse),

    COURTYARD_HOUSE("Courtyard house",
            "Andalusian patio house with 40 cm brick walls: rooms around a glazed gallery and an"
                    + " open-air courtyard.",
            Units.METRES, HousePlans::courtyardHouse),

    MODERN_GLASS_VILLA("Modern glass villa",
            "T-shaped concrete villa: glazed open-plan day wing, cinema and a glass gallery serving"
                    + " the bedroom wing.",
            Units.METRES, HousePlans::modernGlassVilla),

    NORDIC_TIMBER_HOUSE("Nordic timber house",
            "Long timber house with an open-plan day zone, masonry fireplace, sauna and three bedrooms.",
            Units.METRES, HousePlans::nordicTimberHouse),

    STONE_FARMHOUSE("Stone farmhouse",
            "U-shaped farmhouse with 50 cm stone walls around a walled yard, glazed gallery,"
                    + " workshop and garage.",
            Units.METRES, HousePlans::stoneFarmhouse),

    CONCRETE_BLOCK_HOUSE("Concrete block house",
            "Deep-plan family house in concrete block: great room, kitchen and dining far from the"
                    + " windows, internal garage.",
            Units.METRES, HousePlans::concreteBlockHouse),

    VILLA_WITH_GUEST_HOUSE("Villa with guest house",
            "Brick villa with three bedrooms and a detached guest studio on the far side of the pool.",
            Units.METRES, HousePlans::villaWithGuestHouse),

    SEMI_DETACHED_PAIR("Semi-detached pair",
            "Two mirrored three-bedroom homes sharing a concrete party wall: tests interference"
                    + " between neighbours.",
            Units.METRES, HousePlans::semiDetachedPair),

    TWO_WING_COUNTRY_HOUSE("Two-wing country house",
            "Day wing and night wing joined by a glass entrance gallery, with four bedrooms.",
            Units.METRES, HousePlans::twoWingCountryHouse),

    HOTEL_FLOOR("Hotel floor",
            "Central corridor with repeated rooms, useful to analyse linear coverage.",
            plan -> {
                plan.rect(1, 1, 33, 29, CONCRETE, 18);
                plan.wall(1, 12, 33, 12, DRYWALL, 8);
                plan.wall(1, 18, 33, 18, DRYWALL, 8);
                for (double x : new double[] { 7.0, 13.0, 19.0, 25.0 }) {
                    plan.wall(x, 18, x, 29, DRYWALL, 8);
                    plan.wall(x, 1, x, 12, DRYWALL, 8);
                }
                plan.wall(27, 18, 27, 29, GLASS, 4);
                plan.wall(27, 1, 27, 12, GLASS, 4);
            }),

    HOTEL_SUITE("Hotel suite",
            "Large suite with living room, bedroom, dressing room and bathroom mixing glass and drywall.",
            plan -> {
                plan.rect(3, 3, 31, 24, BRICK, 12);
                plan.wall(17, 3, 17, 24, DRYWALL, 8);
                plan.wall(17, 14, 31, 14, DRYWALL, 8);
                plan.wall(23, 14, 23, 24, GLASS, 5);
                plan.wall(8, 10, 17, 10, WOOD, 6);
                plan.wall(8, 3, 8, 10, WOOD, 6);
            }),

    OPEN_PLAN_OFFICE("Open-plan office",
            "Open space with glass meeting rooms and a service core on one side.",
            plan -> {
                plan.rect(1, 1, 34, 24, CONCRETE, 15);
                plan.rect(3, 15, 10, 23, GLASS, 4);
                plan.rect(12, 15, 19, 23, GLASS, 4);
                plan.rect(21, 15, 28, 23, GLASS, 4);
                plan.rect(29, 4, 33, 14, DRYWALL, 8);
                plan.wall(3, 10, 28, 10, WOOD, 5);
            }),

    CELLULAR_OFFICE("Cellular office",
            "Small offices on both sides of a central corridor, useful to compare partition losses.",
            plan -> {
                plan.rect(1, 1, 34, 26, CONCRETE, 15);
                plan.wall(15, 1, 15, 26, DRYWALL, 8);
                plan.wall(19, 1, 19, 26, DRYWALL, 8);
                for (double y : new double[] { 6.0, 11.0, 16.0, 21.0 }) {
                    plan.wall(1, y, 15, y, DRYWALL, 8);
                    plan.wall(19, y, 34, y, DRYWALL, 8);
                }
                plan.rect(15, 20, 19, 26, GLASS, 4);
            }),

    CLINIC_WING("Clinic wing",
            "Clinic wing with treatment bays and consulting rooms around a central corridor.",
            plan -> {
                plan.rect(1, 1, 33, 27, CONCRETE, 16);
                plan.wall(1, 13, 33, 13, DRYWALL, 8);
                plan.wall(1, 17, 33, 17, DRYWALL, 8);
                plan.wall(9, 1, 9, 13, DRYWALL, 8);
                plan.wall(17, 1, 17, 13, DRYWALL, 8);
                plan.wall(25, 1, 25, 13, DRYWALL, 8);
                plan.wall(9, 17, 9, 27, DRYWALL, 8);
                plan.wall(17, 17, 17, 27, DRYWALL, 8);
                plan.wall(25, 17, 25, 27, DRYWALL, 8);
                plan.rect(13, 13, 21, 17, GLASS, 4);
            }),

    CLASSROOM_AND_LAB("Classroom and lab",
            "Training centre with a classroom, a laboratory and a technical storeroom.",
            plan -> {
                plan.rect(2, 2, 32, 24, BRICK, 12);
                plan.wall(2, 14, 32, 14, DRYWALL, 8);
                plan.wall(10, 2, 10, 14, DRYWALL, 8);
                plan.wall(22, 14, 22, 24, DRYWALL, 8);
                plan.wall(26, 14, 26, 24, WOOD, 6);
                plan.wall(10, 8, 22, 8, GLASS, 4);
            }),

    WAREHOUSE_WITH_AISLES("Warehouse with aisles",
            "Warehouse with parallel metal shelving and an office block at one end.",
            plan -> {
                plan.rect(1, 1, 34, 29, CONCRETE, 20);
                plan.rect(2, 2, 9, 8, DRYWALL, 8);
                for (double x : new double[] { 10.0, 14.0, 18.0, 22.0, 26.0, 30.0 }) {
                    plan.wall(x, 5, x, 13, METAL_DOOR, 4);
                    plan.wall(x, 17, x, 26, METAL_DOOR, 4);
                }
                plan.wall(9, 10, 34, 10, WOOD, 5);
            }),

    FACTORY_HALL("Factory hall",
            "Industrial hall with machinery cells, technical rooms and a wide internal route.",
            plan -> {
                plan.rect(1, 1, 34, 29, CONCRETE, 20);
                plan.rect(2, 2, 9, 10, BRICK, 12);
                plan.rect(2, 12, 9, 20, BRICK, 12);
                plan.rect(12, 4, 18, 11, METAL_DOOR, 4);
                plan.rect(21, 4, 28, 11, METAL_DOOR, 4);
                plan.rect(12, 16, 18, 24, METAL_DOOR, 4);
                plan.rect(21, 16, 28, 24, METAL_DOOR, 4);
                plan.wall(9, 14, 34, 14, WOOD, 5);
            });

    /** How the coordinates of a layout are given. */
    private enum Units {
        /** Drawn on a compact grid and enlarged to realistic room sizes. */
        GRID(1.30),
        /** Drawn to scale, in metres. */
        METRES(1.0);

        private final double scale;

        Units(double scale) {
            this.scale = scale;
        }
    }

    private final String displayName;
    private final String description;
    private final Units units;
    private final Consumer<PlanBuilder> layout;

    FloorPlanTemplate(String displayName, String description, Consumer<PlanBuilder> layout) {
        this(displayName, description, Units.GRID, layout);
    }

    FloorPlanTemplate(String displayName, String description, Units units, Consumer<PlanBuilder> layout) {
        this.displayName = displayName;
        this.description = description;
        this.units = units;
        this.layout = layout;
    }

    /** The template loaded in a new project. */
    public static FloorPlanTemplate defaultTemplate() {
        return TWO_BEDROOM_APARTMENT;
    }

    /** Name shown in the UI. */
    public String displayName() {
        return displayName;
    }

    /** One-sentence description of the layout. */
    public String description() {
        return description;
    }

    /** A fresh list of new wall instances, in metres. */
    public List<Wall> walls() {
        return build().walls().stream().map(wall -> wall.scaled(units.scale)).toList();
    }

    /** Names of the rooms and where to write them, in metres; empty if the rooms are not named. */
    public List<RoomLabel> rooms() {
        return build().rooms().stream()
                .map(room -> new RoomLabel(room.name(), room.x() * units.scale, room.y() * units.scale))
                .toList();
    }

    private PlanBuilder build() {
        PlanBuilder builder = new PlanBuilder();
        layout.accept(builder);
        return builder;
    }

    @Override
    public String toString() {
        return displayName;
    }
}
