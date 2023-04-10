import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace SymmetricDifferenceFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        operands: p.Property<Filter[]>;
    };
}
export interface SymmetricDifferenceFilter extends SymmetricDifferenceFilter.Attrs {
}
export declare class SymmetricDifferenceFilter extends Filter {
    properties: SymmetricDifferenceFilter.Props;
    constructor(attrs?: Partial<SymmetricDifferenceFilter.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=symmetric_difference_filter.d.ts.map