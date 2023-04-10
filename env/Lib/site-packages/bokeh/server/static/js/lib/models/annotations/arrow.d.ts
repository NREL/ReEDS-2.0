import { DataAnnotation, DataAnnotationView } from "./data_annotation";
import { ArrowHead, ArrowHeadView } from "./arrow_head";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Context2d } from "../../core/util/canvas";
import { LineVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { CoordinateUnits } from "../../core/enums";
import { FloatArray, ScreenArray } from "../../core/types";
import { IterViews } from "../../core/build_views";
import * as p from "../../core/properties";
export declare class ArrowView extends DataAnnotationView {
    model: Arrow;
    visuals: Arrow.Visuals;
    protected start: ArrowHeadView | null;
    protected end: ArrowHeadView | null;
    protected _x_start: FloatArray;
    protected _y_start: FloatArray;
    protected _x_end: FloatArray;
    protected _y_end: FloatArray;
    protected _sx_start: ScreenArray;
    protected _sy_start: ScreenArray;
    protected _sx_end: ScreenArray;
    protected _sy_end: ScreenArray;
    protected _angles: ScreenArray;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    set_data(source: ColumnarDataSource): void;
    remove(): void;
    map_data(): void;
    paint(ctx: Context2d): void;
}
export declare namespace Arrow {
    type Attrs = p.AttrsOf<Props>;
    type Props = DataAnnotation.Props & {
        x_start: p.XCoordinateSpec;
        y_start: p.YCoordinateSpec;
        start_units: p.Property<CoordinateUnits>;
        start: p.Property<ArrowHead | null>;
        x_end: p.XCoordinateSpec;
        y_end: p.YCoordinateSpec;
        end_units: p.Property<CoordinateUnits>;
        end: p.Property<ArrowHead | null>;
    } & Mixins;
    type Mixins = LineVector;
    type Visuals = DataAnnotation.Visuals & {
        line: visuals.LineVector;
    };
}
export interface Arrow extends Arrow.Attrs {
}
export declare class Arrow extends DataAnnotation {
    properties: Arrow.Props;
    __view_type__: ArrowView;
    constructor(attrs?: Partial<Arrow.Attrs>);
}
//# sourceMappingURL=arrow.d.ts.map