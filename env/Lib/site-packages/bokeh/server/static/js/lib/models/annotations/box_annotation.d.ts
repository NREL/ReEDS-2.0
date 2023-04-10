import { Annotation, AnnotationView } from "./annotation";
import { AutoRanged, auto_ranged } from "../ranges/data_range1d";
import * as mixins from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { SerializableState } from "../../core/view";
import { CoordinateUnits } from "../../core/enums";
import * as p from "../../core/properties";
import { BBox, LRTB, Corners, CoordinateMapper } from "../../core/util/bbox";
import { PanEvent, PinchEvent, Pannable, Pinchable, MoveEvent, Moveable, KeyModifiers } from "../../core/ui_events";
import { Signal } from "../../core/signaling";
import { Rect } from "../../core/types";
import { BorderRadius } from "../common/kinds";
export declare const EDGE_TOLERANCE = 2.5;
type Resizable = typeof Resizable["__type__"];
declare const Resizable: import("../../core/kinds").Kinds.Enum<"left" | "right" | "top" | "bottom" | "none" | "all" | "x" | "y">;
type Movable = typeof Movable["__type__"];
declare const Movable: import("../../core/kinds").Kinds.Enum<"none" | "both" | "x" | "y">;
export declare class BoxAnnotationView extends AnnotationView implements Pannable, Pinchable, Moveable, AutoRanged {
    model: BoxAnnotation;
    visuals: BoxAnnotation.Visuals;
    bbox: BBox;
    serializable_state(): SerializableState;
    connect_signals(): void;
    readonly [auto_ranged] = true;
    bounds(): Rect;
    log_bounds(): Rect;
    get mappers(): LRTB<CoordinateMapper>;
    protected _render(): void;
    get border_radius(): Corners<number>;
    protected _paint_box(): void;
    interactive_bbox(): BBox;
    interactive_hit(sx: number, sy: number): boolean;
    private _hit_test;
    get resizable(): LRTB<boolean>;
    private _can_hit;
    private _pan_state;
    _pan_start(ev: PanEvent): boolean;
    _pan(ev: PanEvent): void;
    _pan_end(ev: PanEvent): void;
    private _pinch_state;
    _pinch_start(ev: PinchEvent): boolean;
    _pinch(ev: PinchEvent): void;
    _pinch_end(ev: PinchEvent): void;
    private get _has_hover();
    private _is_hovered;
    _move_start(_ev: MoveEvent): boolean;
    _move(_ev: MoveEvent): void;
    _move_end(_ev: MoveEvent): void;
    cursor(sx: number, sy: number): string | null;
}
export declare namespace BoxAnnotation {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & {
        top: p.Property<number | null>;
        bottom: p.Property<number | null>;
        left: p.Property<number | null>;
        right: p.Property<number | null>;
        top_units: p.Property<CoordinateUnits>;
        bottom_units: p.Property<CoordinateUnits>;
        left_units: p.Property<CoordinateUnits>;
        right_units: p.Property<CoordinateUnits>;
        border_radius: p.Property<BorderRadius>;
        editable: p.Property<boolean>;
        resizable: p.Property<Resizable>;
        movable: p.Property<Movable>;
        symmetric: p.Property<boolean>;
        tl_cursor: p.Property<string>;
        tr_cursor: p.Property<string>;
        bl_cursor: p.Property<string>;
        br_cursor: p.Property<string>;
        ew_cursor: p.Property<string>;
        ns_cursor: p.Property<string>;
        in_cursor: p.Property<string>;
    } & Mixins;
    type Mixins = mixins.Line & mixins.Fill & mixins.Hatch & mixins.HoverLine & mixins.HoverFill & mixins.HoverHatch;
    type Visuals = Annotation.Visuals & {
        line: visuals.Line;
        fill: visuals.Fill;
        hatch: visuals.Hatch;
        hover_line: visuals.Line;
        hover_fill: visuals.Fill;
        hover_hatch: visuals.Hatch;
    };
}
export interface BoxAnnotation extends BoxAnnotation.Attrs {
}
export declare class BoxAnnotation extends Annotation {
    properties: BoxAnnotation.Props;
    __view_type__: BoxAnnotationView;
    constructor(attrs?: Partial<BoxAnnotation.Attrs>);
    readonly pan: Signal<["pan" | "pan:start" | "pan:end", KeyModifiers], this>;
    update({ left, right, top, bottom }: LRTB<number | null>): void;
    clear(): void;
}
export {};
//# sourceMappingURL=box_annotation.d.ts.map