from runguard.cli.main import main


def test_cli_main_output(capsys)->None:
    main()
    
    captured = capsys.readouterr()
    
    assert "Hello from runguard!" in captured.out