#version 330 core

in vec2 tex_coord;

out vec4 frag_color;

uniform sampler2D pdf_texture;

void main()
{
    /* frag_color = vec4(1.0f, 0.5f, 0.2f, 1.0f); */
    frag_color = texture(pdf_texture, tex_coord);
} 
