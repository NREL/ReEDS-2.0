import { Annotation, AnnotationView } from "./annotation";
import * as mixins from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { CoordinateUnits, Dimension } from "../../core/enums";
import { PanEvent, Pannable, MoveEvent, Moveable, KeyModifiers } from "../../core/ui_events";
import { Signal } from "../../core/signaling";
import * as p from "../../core/properties";
type Point = {
    x: number;
    y: number;
};
declare class Line {
    readonly p0: Point;
    readonly p1: Point;
    constructor(p0: Point, p1: Point);
    clone(): Line;
    hit_test(pt: Point, tolerance?: number): boolean;
    translate(dx: number, dy: number): Line;
}
export declare class SpanView extends AnnotationView implements Pannable, Moveable {
    model: Span;
    visuals: Span.Visuals;
    protected line: Line;
    connect_signals(): void;
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
export declare namespace Span {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & {
        location: p.Property<number | null>;
        location_units: p.Property<CoordinateUnits>;
        dimension: p.Property<Dimension>;
        editable: p.Property<boolean>;
    } & Mixins;
    type Mixins = mixins.Line & mixins.HoverLine;
    type Visuals = Annotation.Visuals & {
        line: visuals.Line;
        hover_line: visuals.Line;
    };
}
export interface Span extends Span.Attrs {
}
export declare class Span extends Annotation {
    properties: Span.Props;
    __view_type__: SpanView;
    constructor(attrs?: Partial<Span.Attrs>);
    readonly pan: Signal<["pan" | "pan:start" | "pan:end", KeyModifiers], this>;
}
export {};
//# sourceMappingURL=span.d.ts.map