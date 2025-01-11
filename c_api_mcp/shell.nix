let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-24.05";
  pkgs = import nixpkgs { config = {}; overlays = []; };
in

pkgs.mkShellNoCC {
  packages = with pkgs; [
    pkgs.python312Full
    pkgs.python312Packages.numpy
    pkgs.python312Packages.scipy
    pkgs.python312Packages.pyopengl # Note I also needed https://github.com/nix-community/nixGL
    pkgs.python312Packages.pyopengl-accelerate
    pkgs.python312Packages.pymupdf
    pkgs.python312Packages.pillow

    pkg-config

    # lsp
    pkgs.python312Packages.python-lsp-server
    pkgs.python312Packages.pylsp-rope
    pkgs.python312Packages.pyflakes
    pkgs.python312Packages.pycodestyle
  ];
}
