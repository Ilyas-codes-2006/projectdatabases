{
  description = "Development environment voor Project databases";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
                  buildInputs = with pkgs; [
                    python312
                    python312Packages.pip
                    python312Packages.virtualenv
                    libpq
                    pkg-config
                    nodejs_22
                    nodePackages.npm
                    esbuild # 👈 ADDED THIS
                  ];

                  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath (with pkgs; [
                    libpq
                    stdenv.cc.cc.lib
                    zlib
                  ]);

                  # 👈 ADDED THIS: Tell NPM to use the Nix-provided esbuild binary
                  ESBUILD_BINARY_PATH = "${pkgs.esbuild}/bin/esbuild";

                  shellHook = ''
                    echo "===================================================="
                    echo "🚀 Welkom in de Nix development environment!"
                    echo "🐍 Python versie: $(python --version)"
                    echo "📦 Node versie:   $(node --version)"
                    echo "===================================================="

                    if [ ! -d ".venv" ]; then
                      echo "Aanmaken van een nieuwe Python virtual environment (.venv)..."
                      python -m venv .venv
                    fi

                    source .venv/bin/activate

                    echo ""
                    echo "💡 Tip voor backend: 'pip install -r backend/requirements.txt'"
                    echo "💡 Tip voor frontend: 'cd frontend && npm install'"
                    echo "===================================================="
                  '';
                };
      }
    );
}
