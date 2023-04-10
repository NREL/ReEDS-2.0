import { UpperLower, UpperLowerView } from "./upper_lower";
import { ArrowHead, ArrowHeadView } from "./arrow_head";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Context2d } from "../../core/util/canvas";
import { IterViews } from "../../core/build_views";
import { LineVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
export declare class WhiskerView extends UpperLowerView {
    model: Whisker;
    visuals: Whisker.Visuals;
    protected lower_head: ArrowHeadView | null;
    protected upper_head: ArrowHeadView | null;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    set_data(source: ColumnarDataSource): void;
    paint(ctx: Context2d): void;
}
export declare namespace Whisker {
    type Attrs = p.AttrsOf<Props>;
    type Props = UpperLower.Props & {
        lower_head: p.Property<ArrowHead | null>;
        upper_head: p.Property<ArrowHead | null>;
    } & Mixins;
    type Mixins = LineVector;
    type Visuals = UpperLower.Visuals & {
        line: visuals.LineVector;
    };
}
export interface Whisker extends Whisker.Attrs {
}
export declare class Whisker extends UpperLower {
    properties: Whisker.Props;
    __view_type__: WhiskerView;
    constructor(attrs?: Partial<Whisker.Attrs>);
}
//# sourceMappingURL=whisker.d.ts.map