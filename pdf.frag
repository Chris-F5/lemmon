#version 330 core

in vec2 tex_coord;

out vec4 frag_color;

uniform sampler2D pdf_texture;

void main()
{
    frag_color = texture(pdf_texture, tex_coord);
} 
