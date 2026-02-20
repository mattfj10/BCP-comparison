{
  description = "BCP Morning Prayer comparator web server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
        runServer = {
          type = "app";
          program = "${pkgs.writeShellScript "run-bcp-server" ''
            set -euo pipefail
            cd "${self}"
            exec ${python}/bin/python3 app.py
          ''}";
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [ python ];
          shellHook = ''
            echo "BCP comparison dev shell"
            echo "Run: python3 app.py"
          '';
        };

        apps.default = runServer;
        apps.server = runServer;
      });
}
