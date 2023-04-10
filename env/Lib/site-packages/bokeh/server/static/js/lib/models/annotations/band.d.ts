import { UpperLower, UpperLowerView } from "./upper_lower";
import { Context2d } from "../../core/util/canvas";
import * as mixins from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
export declare class BandView extends UpperLowerView {
    model: Band;
    visuals: Band.Visuals;
    paint(ctx: Context2d): void;
}
export declare namespace Band {
    type Attrs = p.AttrsOf<Props>;
    type Props = UpperLower.Props & Mixins;
    type Mixins = mixins.Line & mixins.Fill;
    type Visuals = UpperLower.Visuals & {
        line: visuals.Line;
        fill: visuals.Fill;
    };
}
export interface Band extends Band.Attrs {
}
export declare class Band extends UpperLower {
    properties: Band.Props;
    __view_type__: BandView;
    constructor(attrs?: Partial<Band.Attrs>);
}
//# sourceMappingURL=band.d.ts.map