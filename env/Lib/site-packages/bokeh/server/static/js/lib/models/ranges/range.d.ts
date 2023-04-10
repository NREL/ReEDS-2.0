import { Model } from "../../model";
import type { PlotView } from "../plots/plot";
import * as p from "../../core/properties";
export declare namespace Range {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        bounds: p.Property<[number | null, number | null] | "auto" | null>;
        min_interval: p.Property<number | null>;
        max_interval: p.Property<number | null>;
    };
}
export interface Range extends Range.Attrs {
}
export declare abstract class Range extends Model {
    properties: Range.Props;
    constructor(attrs?: Partial<Range.Attrs>);
    abstract start: number;
    abstract end: number;
    abstract get min(): number;
    abstract get max(): number;
    have_updated_interactively: boolean;
    abstract reset(): void;
    get is_reversed(): boolean;
    get is_valid(): boolean;
    get span(): number;
    /** internal */
    readonly plots: Set<PlotView>;
}
//# sourceMappingURL=range.d.ts.map