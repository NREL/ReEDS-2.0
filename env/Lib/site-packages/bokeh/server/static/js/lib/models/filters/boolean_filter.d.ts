import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace BooleanFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        booleans: p.Property<boolean[] | null>;
    };
}
export interface BooleanFilter extends BooleanFilter.Attrs {
}
export declare class BooleanFilter extends Filter {
    properties: BooleanFilter.Props;
    constructor(attrs?: Partial<BooleanFilter.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=boolean_filter.d.ts.map