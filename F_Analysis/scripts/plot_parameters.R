# plot parameters

# --------------------------------------------------- |
# plot theme ----
# --------------------------------------------------- |

# size of text in plots
large.text.size = 14
small.text.size = 12
text.plot = 14

color.background = "white"
color.grid.major = "gray70"
color.axis.text = "gray30"
color.axis.title = "gray50"
color.title = "gray30"

# plot theme
plot_theme = 
  theme(plot.title=element_text(color=color.title, size=large.text.size, vjust=1.25),
        panel.background=element_rect(fill=color.background, color=color.background),
        plot.background=element_rect(fill=color.background, color=color.background),
        #panel.border=element_rect(color=color.background),
        panel.grid.major.y=element_line(color=color.grid.major,size=.25,linetype='dashed'),
        panel.grid.major.x=element_blank(),
        panel.grid.minor=element_blank(),
        strip.background = element_rect(fill="white"),
        strip.text = element_text(size=small.text.size, color = color.axis.text),
        legend.key = element_rect(color = "grey80", size = 0.8), 
        legend.key.size = grid::unit(1.5, "lines"),
        legend.text = element_text(size = small.text.size, color = color.axis.text, margin = margin(l = 5)), 
        legend.title = element_blank(), 
        axis.text.x= element_text(size=small.text.size,color=color.axis.text),
        axis.text.y= element_text(size=small.text.size,color=color.axis.text),
        axis.title.x= element_text(size=small.text.size,color=color.axis.text,vjust=0),
        axis.title.y = element_text(size=small.text.size, color=color.axis.title,angle=0,vjust=0.5),
        axis.ticks.x = element_line(color=color.grid.major),
        axis.ticks.length.x = grid::unit(0.5, "lines"),
        axis.ticks.y=element_blank(),
        panel.spacing = unit(0.5, "lines")) 

