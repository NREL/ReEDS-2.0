import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { PointGeometry } from "../../core/geometry";
import * as mixins from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
import { XY, LRTB, Corners } from "../../core/util/bbox";
import { Rect } from "../../core/util/affine";
import { TextBox } from "../../core/graphics";
import { TextAnchor, BorderRadius, Padding } from "../common/kinds";
declare class TextAnchorSpec extends p.DataSpec<TextAnchor> {
}
export type TextData = XYGlyphData & p.UniformsOf<Text.Mixins> & {
    readonly text: p.Uniform<string | null>;
    readonly angle: p.Uniform<number>;
    readonly x_offset: p.Uniform<number>;
    readonly y_offset: p.Uniform<number>;
    readonly anchor: p.Uniform<TextAnchor>;
    labels: (TextBox | null)[];
    swidth: Float32Array;
    sheight: Float32Array;
    anchor_: p.Uniform<XY<number>>;
    padding: LRTB<number>;
    border_radius: Corners<number>;
};
export interface TextView extends TextData {
}
export declare class TextView extends XYGlyphView {
    model: Text;
    visuals: Text.Visuals;
    protected _set_data(indices: number[] | null): void;
    after_visuals(): void;
    protected _render(ctx: Context2d, indices: number[], data?: TextData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    rect_i(i: number): Rect;
    scenterxy(i: number): [number, number];
}
export declare namespace Text {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        text: p.NullStringSpec;
        angle: p.AngleSpec;
        x_offset: p.NumberSpec;
        y_offset: p.NumberSpec;
        anchor: TextAnchorSpec;
        padding: p.Property<Padding>;
        border_radius: p.Property<BorderRadius>;
    } & Mixins;
    type Mixins = mixins.TextVector & mixins.BorderLineVector & mixins.BackgroundFillVector & mixins.BackgroundHatchVector;
    type Visuals = XYGlyph.Visuals & {
        text: visuals.TextVector;
        border_line: visuals.LineVector;
        background_fill: visuals.FillVector;
        background_hatch: visuals.HatchVector;
    };
}
export interface Text extends Text.Attrs {
}
export declare class Text extends XYGlyph {
    properties: Text.Props;
    __view_type__: TextView;
    constructor(attrs?: Partial<Text.Attrs>);
}
export {};
//# sourceMappingURL=text.d.ts.map