{pkgs ? import <nixpkgs> {}, ...}:
pkgs.mkShellNoCC {
  packages = with pkgs; [
    # deployment
    ansible
    gnumake

    # for mrpack.py
    (python3.withPackages (p:
      with p; [
        requests
        pyyaml
        # rcon awaiting merge @ https://github.com/NixOS/nixpkgs/pull/423385
      ]))
    
    # discord bot
    go
  ];
}
