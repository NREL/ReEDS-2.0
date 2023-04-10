import { Filter } from "./filter";
import * as p from "../../core/properties";
import { Indices } from "../../core/types";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace DifferenceFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        operands: p.Property<Filter[]>;
    };
}
export interface DifferenceFilter extends DifferenceFilter.Attrs {
}
export declare class DifferenceFilter extends Filter {
    properties: DifferenceFilter.Props;
    constructor(attrs?: Partial<DifferenceFilter.Attrs>);
    compute_indices(source: ColumnarDataSource): Indices;
}
//# sourceMappingURL=difference_filter.d.ts.map