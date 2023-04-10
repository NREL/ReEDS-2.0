import { Annotation, AnnotationView } from "./annotation";
import { AutoRanged, auto_ranged } from "../ranges/data_range1d";
import * as mixins from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { SerializableState } from "../../core/view";
import { CoordinateUnits } from "../../core/enums";
import { Arrayable, Rect } from "../../core/types";
import { Signal } from "../../core/signaling";
import { PanEvent, Pannable, MoveEvent, Moveable, KeyModifiers } from "../../core/ui_events";
import { BBox, CoordinateMapper } from "../../core/util/bbox";
import * as p from "../../core/properties";
export type Node = {
    type: "node";
    i: number;
};
export type Edge = {
    type: "edge";
    i: number;
};
export type Area = {
    type: "area";
};
export type HitTarget = Node | Edge | Area;
type Point = {
    x: number;
    y: number;
};
declare class Polygon {
    readonly xs: Arrayable<number>;
    readonly ys: Arrayable<number>;
    constructor(xs?: Arrayable<number>, ys?: Arrayable<number>);
    clone(): Polygon;
    [Symbol.iterator](): Iterator<[number, number, number]>;
    nodes(): IterableIterator<[number, number, number]>;
    edges(): IterableIterator<[Point, Point, number]>;
    contains(x: number, y: number): boolean;
    get bbox(): BBox;
    get n(): number;
    translate(dx: number, dy: number, ...i: number[]): Polygon;
}
export declare class PolyAnnotationView extends AnnotationView implements Pannable, Moveable, AutoRanged {
    model: PolyAnnotation;
    visuals: PolyAnnotation.Visuals;
    protected poly: Polygon;
    serializable_state(): SerializableState;
    connect_signals(): void;
    readonly [auto_ranged] = true;
    bounds(): Rect;
    log_bounds(): Rect;
    protected _mappers(): {
        x: CoordinateMapper;
        y: CoordinateMapper;
    };
    protected _render(): void;
    interactive_hit(sx: number, sy: number): boolean;
    private _hit_test;
    private _can_hit;
    private _pan_state;
    _pan_start(ev: PanEvent): boolean;
    _pan(ev: PanEvent): void;
    _pan_end(ev: PanEvent): void;
    private get _has_hover();
    private _is_hovered;
    _move_start(_ev: MoveEvent): boolean;
    _move(_ev: MoveEvent): void;
    _move_end(_ev: MoveEvent): void;
    cursor(sx: number, sy: number): string | null;
}
export declare namespace PolyAnnotation {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & {
        xs: p.Property<Arrayable<number>>;
        ys: p.Property<Arrayable<number>>;
        xs_units: p.Property<CoordinateUnits>;
        ys_units: p.Property<CoordinateUnits>;
        editable: p.Property<boolean>;
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
export interface PolyAnnotation extends PolyAnnotation.Attrs {
}
export declare class PolyAnnotation extends Annotation {
    properties: PolyAnnotation.Props;
    __view_type__: PolyAnnotationView;
    constructor(attrs?: Partial<PolyAnnotation.Attrs>);
    readonly pan: Signal<["pan" | "pan:start" | "pan:end", KeyModifiers], this>;
    update({ xs, ys }: {
        xs: Arrayable<number>;
        ys: Arrayable<number>;
    }): void;
    clear(): void;
}
export {};
//# sourceMappingURL=poly_annotation.d.ts.map