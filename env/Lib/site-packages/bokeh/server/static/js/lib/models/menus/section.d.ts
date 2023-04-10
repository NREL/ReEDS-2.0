import { MenuItem, MenuItemView } from "./menu_item";
import * as p from "../../core/properties";
export declare class SectionView extends MenuItemView {
    model: Section;
    render(): void;
}
export declare namespace Section {
    type Attrs = p.AttrsOf<Props>;
    type Props = MenuItem.Props & {
        items: p.Property<MenuItem[]>;
    };
}
export interface Section extends Section.Attrs {
}
export declare class Section extends MenuItem {
    properties: Section.Props;
    __view_type__: SectionView;
    constructor(attrs?: Partial<Section.Attrs>);
}
//# sourceMappingURL=section.d.ts.map