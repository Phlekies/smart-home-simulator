package io.github.phlekies.smarthome.model.template;

/**
 * Name of a room of a template and the point, in metres, where it is written on the plan.
 *
 * @param name room name, such as "Kitchen"
 * @param x    x of the label centre in metres
 * @param y    y of the label centre in metres
 */
public record RoomLabel(String name, double x, double y) {
}
