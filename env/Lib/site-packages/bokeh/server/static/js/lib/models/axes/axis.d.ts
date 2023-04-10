import { GuideRenderer, GuideRendererView } from "../renderers/guide_renderer";
import { Ticker } from "../tickers/ticker";
import { TickFormatter } from "../formatters/tick_formatter";
import { LabelingPolicy } from "../policies/labeling";
import { Range } from "../ranges/range";
import * as visuals from "../../core/visuals";
import * as mixins from "../../core/property_mixins";
import * as p from "../../core/properties";
import { SerializableState } from "../../core/view";
import { Side, TickLabelOrientation } from "../../core/enums";
import { Size, Layoutable } from "../../core/layout";
import { Panel, Orient } from "../../core/layout/side_panel";
import { Context2d } from "../../core/util/canvas";
import { GraphicsBoxes } from "../../core/graphics";
import { Factor } from "../ranges/factor_range";
import { BaseTextView } from "../text/base_text";
import { BaseText } from "../text/base_text";
import { IterViews } from "../../core/build_views";
export type Extents = {
    tick: number;
    tick_labels: number[];
    tick_label: number;
    axis_label: number;
};
export type Coords = [number[], number[]];
export interface TickCoords {
    major: Coords;
    minor: Coords;
}
export declare class AxisView extends GuideRendererView {
    model: Axis;
    visuals: Axis.Visuals;
    panel: Panel;
    layout: Layoutable;
    _axis_label_view: BaseTextView | null;
    _major_label_views: Map<string | number, BaseTextView>;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    protected _init_axis_label(): Promise<void>;
    protected _init_major_labels(): Promise<void>;
    update_layout(): void;
    get_size(): Size;
    get is_renderable(): boolean;
    protected _render(): void;
    protected _paint?(ctx: Context2d, extents: Extents, tick_coords: TickCoords): void;
    connect_signals(): void;
    get needs_clip(): boolean;
    protected _draw_rule(ctx: Context2d, _extents: Extents): void;
    protected _draw_major_ticks(ctx: Context2d, _extents: Extents, tick_coords: TickCoords): void;
    protected _draw_minor_ticks(ctx: Context2d, _extents: Extents, tick_coords: TickCoords): void;
    protected _draw_major_labels(ctx: Context2d, extents: Extents, tick_coords: TickCoords): void;
    protected _axis_label_extent(): number;
    protected _draw_axis_label(ctx: Context2d, extents: Extents, _tick_coords: TickCoords): void;
    protected _draw_ticks(ctx: Context2d, coords: Coords, tin: number, tout: number, visuals: visuals.Line): void;
    protected _draw_oriented_labels(ctx: Context2d, labels: GraphicsBoxes, coords: Coords, orient: Orient | number, _side: Side, standoff: number, visuals: visuals.Text): void;
    _tick_extent(): number;
    protected _tick_label_extents(): number[];
    get extents(): Extents;
    protected _oriented_labels_extent(labels: GraphicsBoxes, orient: Orient | number, standoff: number, visuals: visuals.Text): number;
    get normals(): [number, number];
    get dimension(): 0 | 1;
    compute_labels(ticks: number[]): GraphicsBoxes;
    get offsets(): [number, number];
    get ranges(): [Range, Range];
    get computed_bounds(): [number, number];
    get rule_coords(): Coords;
    get tick_coords(): TickCoords;
    get loc(): number;
    serializable_state(): SerializableState;
    remove(): void;
    has_finished(): boolean;
}
export declare namespace Axis {
    type Attrs = p.AttrsOf<Props>;
    type Props = GuideRenderer.Props & {
        bounds: p.Property<[number, number] | "auto">;
        ticker: p.Property<Ticker>;
        formatter: p.Property<TickFormatter>;
        axis_label: p.Property<string | BaseText | null>;
        axis_label_standoff: p.Property<number>;
        major_label_standoff: p.Property<number>;
        major_label_orientation: p.Property<TickLabelOrientation | number>;
        major_label_overrides: p.Property<Map<string | number, string | BaseText>>;
        major_label_policy: p.Property<LabelingPolicy>;
        major_tick_in: p.Property<number>;
        major_tick_out: p.Property<number>;
        minor_tick_in: p.Property<number>;
        minor_tick_out: p.Property<number>;
        fixed_location: p.Property<number | Factor | null>;
    } & Mixins;
    type Mixins = mixins.AxisLine & mixins.MajorTickLine & mixins.MinorTickLine & mixins.MajorLabelText & mixins.AxisLabelText;
    type Visuals = GuideRenderer.Visuals & {
        axis_line: visuals.Line;
        major_tick_line: visuals.Line;
        minor_tick_line: visuals.Line;
        major_label_text: visuals.Text;
        axis_label_text: visuals.Text;
    };
}
export interface Axis extends Axis.Attrs {
}
export declare class Axis extends GuideRenderer {
    properties: Axis.Props;
    __view_type__: AxisView;
    constructor(attrs?: Partial<Axis.Attrs>);
}
//# sourceMappingURL=axis.d.ts.map