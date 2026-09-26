{
  description = "tmux copy-mode cursor reproducer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    tmux-src = {
      url = "github:tmux/tmux/94796f6b1182507efac8a272fc309a79e22e58a5";
      flake = false;
    };
  };

  outputs = { nixpkgs, tmux-src, ... }: {
    packages = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        tmux = pkgs.tmux.overrideAttrs {
          version = "next-3.9";
          src = tmux-src;
        };
        patched = tmux.overrideAttrs (old: {
          postPatch = (old.postPatch or "") + ''
            substituteInPlace server-client.c --replace-fail \
              'pane_mode = wp->base.mode;' 'pane_mode = s->mode;'
          '';
        });
        reproduce = binary: pkgs.writeShellScriptBin "tmux-repro" ''
          exec ${pkgs.python3}/bin/python3 ${./repro.py} \
            --producer ${./producer.py} --revision ${tmux-src.rev} \
            ${binary}/bin/tmux "$@"
        '';
      in {
        default = reproduce tmux;
        patched = reproduce patched;
      });
  };
}
